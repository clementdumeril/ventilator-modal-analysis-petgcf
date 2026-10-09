"""VTK renders of the shock cases (displacement with several warp scales, von Mises hot spots).
"""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import vtk


ROOT = Path(__file__).resolve().parents[1]
VTM_DIR = ROOT / "03_VISUALISATION_PARAVIEW"
FIG_DIR = ROOT / "01_RAPPORT_LATEX" / "figures"

CASES = {
    "cyl_ymin": {
        "label": "Lateral impact Y-",
        "peak_file": VTM_DIR / "cyl_ymin" / "cyl_ymin_t0002500us.vtm",
        "critical": (-8.7, -133.7, 144.4),
    },
    "cyl_ymax": {
        "label": "Lateral impact Y+",
        "peak_file": VTM_DIR / "cyl_ymax" / "cyl_ymax_t0002500us.vtm",
        "critical": (30.2, -15.3, 181.9),
    },
    "cyl_oblique_ymin_z": {
        "label": "Oblique impact Y- + Z",
        "peak_file": VTM_DIR / "cyl_oblique_ymin_z" / "cyl_oblique_ymin_z_t0002000us.vtm",
        "depl_file": VTM_DIR / "cyl_oblique_ymin_z" / "cyl_oblique_ymin_z_t0002500us.vtm",
        "critical": (99.2, -131.2, 161.7),
    },
}


def first_dataset(obj):
    if isinstance(obj, vtk.vtkDataSet):
        return obj
    if isinstance(obj, vtk.vtkCompositeDataSet):
        iterator = obj.NewIterator()
        iterator.UnRegister(None)
        iterator.InitTraversal()
        while not iterator.IsDoneWithTraversal():
            child = iterator.GetCurrentDataObject()
            dataset = first_dataset(child)
            if dataset is not None:
                return dataset
            iterator.GoToNextItem()
    return None


def load_dataset(path: Path) -> vtk.vtkDataSet:
    reader = vtk.vtkXMLMultiBlockDataReader()
    reader.SetFileName(str(path))
    reader.Update()
    dataset = first_dataset(reader.GetOutput())
    if dataset is None:
        raise RuntimeError(f"No dataset found in {path}")
    return dataset


def get_range(dataset: vtk.vtkDataSet, array_name: str, point_data: bool = True) -> tuple[float, float]:
    data = dataset.GetPointData() if point_data else dataset.GetCellData()
    arr = data.GetArray(array_name)
    if arr is None:
        raise KeyError(array_name)
    return arr.GetRange()


def surface_dataset(dataset: vtk.vtkDataSet) -> vtk.vtkPolyData:
    surf = vtk.vtkDataSetSurfaceFilter()
    surf.SetInputData(dataset)
    surf.Update()
    return surf.GetOutput()


def warp_dataset(dataset: vtk.vtkDataSet, scale: float) -> vtk.vtkDataSet:
    if scale == 0.0:
        return dataset
    warp = vtk.vtkWarpVector()
    warp.SetInputData(dataset)
    warp.SetInputArrayToProcess(0, 0, 0, vtk.vtkDataObject.FIELD_ASSOCIATION_POINTS, "DEPL_mm")
    warp.SetScaleFactor(scale)
    warp.Update()
    return warp.GetOutput()


def make_lut(array_range: tuple[float, float], mode: str) -> vtk.vtkLookupTable:
    lut = vtk.vtkLookupTable()
    lut.SetNumberOfTableValues(256)
    lut.SetRange(*array_range)
    if mode == "depl":
        # Blue -> cyan -> pale yellow -> orange/red.
        colors = [
            (0.02, 0.08, 0.45),
            (0.10, 0.45, 0.85),
            (0.55, 0.86, 0.90),
            (0.95, 0.82, 0.36),
            (0.78, 0.12, 0.05),
        ]
    else:
        # Blue -> white -> red, intentionally capped for stress interpretability.
        colors = [
            (0.02, 0.08, 0.45),
            (0.15, 0.35, 0.85),
            (0.88, 0.92, 0.95),
            (0.95, 0.62, 0.30),
            (0.78, 0.03, 0.02),
        ]
    ctf = vtk.vtkColorTransferFunction()
    for index, color in enumerate(colors):
        value = array_range[0] + (array_range[1] - array_range[0]) * index / (len(colors) - 1)
        ctf.AddRGBPoint(value, *color)
    for i in range(256):
        x = array_range[0] + (array_range[1] - array_range[0]) * i / 255.0
        lut.SetTableValue(i, *ctf.GetColor(x), 1.0)
    lut.Build()
    return lut


def add_scalar_bar(renderer: vtk.vtkRenderer, mapper: vtk.vtkMapper, title: str) -> None:
    bar = vtk.vtkScalarBarActor()
    bar.SetLookupTable(mapper.GetLookupTable())
    bar.SetTitle(title)
    bar.SetNumberOfLabels(5)
    bar.SetMaximumWidthInPixels(80)
    bar.SetMaximumHeightInPixels(360)
    bar.GetTitleTextProperty().SetColor(1, 1, 1)
    bar.GetLabelTextProperty().SetColor(1, 1, 1)
    bar.GetTitleTextProperty().SetFontSize(14)
    bar.GetLabelTextProperty().SetFontSize(12)
    renderer.AddActor2D(bar)


def add_text(renderer: vtk.vtkRenderer, text: str) -> None:
    actor = vtk.vtkTextActor()
    actor.SetInput(text)
    actor.SetPosition(22, 22)
    prop = actor.GetTextProperty()
    prop.SetFontSize(23)
    prop.SetColor(1, 1, 1)
    prop.SetBold(True)
    prop.SetShadow(True)
    renderer.AddActor2D(actor)


def set_camera(
    renderer: vtk.vtkRenderer,
    dataset: vtk.vtkDataSet,
    zoom: float = 1.0,
    focal=None,
    mode: str = "iso",
) -> None:
    bounds = dataset.GetBounds()
    cx = (bounds[0] + bounds[1]) / 2.0
    cy = (bounds[2] + bounds[3]) / 2.0
    cz = (bounds[4] + bounds[5]) / 2.0
    if focal is not None:
        cx, cy, cz = focal
    span = max(bounds[1] - bounds[0], bounds[3] - bounds[2], bounds[5] - bounds[4])
    distance = 2.35 * span / zoom
    camera = renderer.GetActiveCamera()
    camera.SetFocalPoint(cx, cy, cz)
    if mode == "xminus":
        camera.SetPosition(cx - 1.95 * distance, cy - 0.20 * distance, cz + 0.55 * distance)
    elif mode == "xplus":
        camera.SetPosition(cx + 1.95 * distance, cy - 0.20 * distance, cz + 0.55 * distance)
    else:
        camera.SetPosition(cx + 0.95 * distance, cy - 1.45 * distance, cz + 0.78 * distance)
    camera.SetViewUp(0.0, 0.0, 1.0)
    camera.SetViewAngle(28.0)
    renderer.ResetCameraClippingRange()


def render_png(
    input_path: Path,
    output_path: Path,
    scalar: str,
    scalar_range: tuple[float, float],
    scalar_title: str,
    title: str,
    warp_scale: float = 0.0,
    zoom: float = 1.0,
    focal=None,
    mode: str = "vmis",
    camera_mode: str = "iso",
) -> None:
    dataset = load_dataset(input_path)
    warped = warp_dataset(dataset, warp_scale)
    surface = surface_dataset(warped)

    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputData(surface)
    mapper.SetScalarModeToUsePointFieldData()
    mapper.SelectColorArray(scalar)
    mapper.SetScalarRange(*scalar_range)
    mapper.SetLookupTable(make_lut(scalar_range, mode))

    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    actor.GetProperty().SetInterpolationToPhong()
    actor.GetProperty().SetSpecular(0.18)
    actor.GetProperty().SetSpecularPower(20)

    renderer = vtk.vtkRenderer()
    renderer.SetBackground(0.36, 0.34, 0.32)
    renderer.AddActor(actor)
    add_scalar_bar(renderer, mapper, scalar_title)
    add_text(renderer, title)
    set_camera(renderer, surface, zoom=zoom, focal=focal, mode=camera_mode)

    window = vtk.vtkRenderWindow()
    window.SetOffScreenRendering(1)
    window.SetSize(1600, 1200)
    window.AddRenderer(renderer)
    window.Render()

    image = vtk.vtkWindowToImageFilter()
    image.SetInput(window)
    image.SetScale(1)
    image.ReadFrontBufferOff()
    image.Update()

    writer = vtk.vtkPNGWriter()
    writer.SetFileName(str(output_path))
    writer.SetInputConnection(image.GetOutputPort())
    writer.Write()
    print(f"Wrote {output_path}")


def make_scale_composite() -> None:
    paths = [
        FIG_DIR / "render_oblique_depl_scale1.png",
        FIG_DIR / "render_oblique_depl_scale5.png",
        FIG_DIR / "render_oblique_depl_scale12.png",
    ]
    titles = ["Warp x1", "Warp x5", "Warp x12"]
    fig, axes = plt.subplots(1, 3, figsize=(13.5, 4.2))
    for ax, path, title in zip(axes, paths, titles):
        ax.imshow(plt.imread(path))
        ax.set_title(title, fontsize=11)
        ax.axis("off")
    fig.suptitle("Influence of visual deformation scale on the oblique impact interpretation", fontsize=13)
    plt.tight_layout()
    out = FIG_DIR / "render_oblique_deformation_scale_comparison.png"
    plt.savefig(out, dpi=220)
    plt.close()
    print(f"Wrote {out}")


def main() -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)

    for case_id, case in CASES.items():
        render_png(
            input_path=case["peak_file"],
            output_path=FIG_DIR / f"render_{case_id}_vmis_peak.png",
            scalar="VMIS_MPa_node_avg",
            scalar_range=(0.0, 125.0),
            scalar_title="VMIS avg. (MPa)",
            title=f"{case['label']} - Von Mises, capped at 125 MPa",
            warp_scale=0.0,
            zoom=1.0,
            mode="vmis",
        )
        render_png(
            input_path=case["peak_file"],
            output_path=FIG_DIR / f"render_{case_id}_vmis_zoom.png",
            scalar="VMIS_MPa_node_avg",
            scalar_range=(0.0, 125.0),
            scalar_title="VMIS avg. (MPa)",
            title=f"{case['label']} - critical-zone zoom",
            warp_scale=0.0,
            zoom=2.6,
            focal=case["critical"],
            mode="vmis",
        )

    oblique_depl = CASES["cyl_oblique_ymin_z"]["depl_file"]
    for scale in (1.0, 5.0, 12.0):
        render_png(
            input_path=oblique_depl,
            output_path=FIG_DIR / f"render_oblique_depl_scale{int(scale)}.png",
            scalar="DEPL_MAG_mm",
            scalar_range=(0.0, 2.0),
            scalar_title="|u| (mm)",
            title=f"Oblique impact - displacement magnitude, warp x{scale:g}",
            warp_scale=scale,
            zoom=1.0,
            mode="depl",
        )

    render_png(
        input_path=oblique_depl,
        output_path=FIG_DIR / "render_oblique_depl_presentation_xminus.png",
        scalar="DEPL_MAG_mm",
        scalar_range=(0.0, 2.0),
        scalar_title="|u| (mm)",
        title="Oblique impact - presentation view, warp x12",
        warp_scale=12.0,
        zoom=1.25,
        mode="depl",
        camera_mode="xminus",
    )
    render_png(
        input_path=oblique_depl,
        output_path=FIG_DIR / "render_oblique_depl_presentation_xplus.png",
        scalar="DEPL_MAG_mm",
        scalar_range=(0.0, 2.0),
        scalar_title="|u| (mm)",
        title="Oblique impact - alternate front view, warp x12",
        warp_scale=12.0,
        zoom=1.25,
        mode="depl",
        camera_mode="xplus",
    )

    make_scale_composite()


if __name__ == "__main__":
    main()
