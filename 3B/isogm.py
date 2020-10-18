#!/usr/bin/env python

import vtk
import argparse


DEFAULT_COLORMAP = [[0, 1, 1, 1], [2500, 1, 1, 1], [109404, 1, 0, 0]]
DEFAULT_PLANE_POS = [0, 0, 0]


class Visualization(object):
	"""docstring for Visualization"""

	def clipXSliderHandler(self,obj, event):
		self.clip_x = obj.GetRepresentation().GetValue()
		self.updateCT()

	def clipYSliderHandler(self,obj, event):
		self.clip_y = obj.GetRepresentation().GetValue()
		self.updateCT()

	def clipZSliderHandler(self,obj, event):
		self.clip_z = obj.GetRepresentation().GetValue()
		self.updateCT()

	def updateCT(self):
		self.plane_x.SetOrigin((self.clip_x,0,0))
		self.plane_y.SetOrigin(0,self.clip_y,0)
		self.plane_z.SetOrigin(0,0,self.clip_z)
		self.clipper_x.Update()
		self.clipper_y.Update()
		self.clipper_z.Update()

	def __init__(self, args):
		## Files reading and settings
		self.isovalues = args.isoval
		self.cmap = args.cmap

		self.clip_x = args.clip[0]
		self.clip_y = args.clip[1]
		self.clip_z = args.clip[2]

		ct_image = vtk.vtkXMLImageDataReader()
		ct_image.SetFileName(args.data)
		ct_image.Update()

		gm_image = vtk.vtkXMLImageDataReader()
		gm_image.SetFileName(args.gradmag)
		gm_image.Update()

		self.ct_contour = vtk.vtkContourFilter()
		self.ct_contour.SetInputConnection(ct_image.GetOutputPort());
		self.ct_contour.ComputeNormalsOn()

		for i in range(len(self.isovalues)):
			self.ct_contour.SetValue(i, self.isovalues[i])

			
		color_func = vtk.vtkColorTransferFunction()
		color_func.SetColorSpaceToRGB()
		for c in self.cmap:
			color_func.AddRGBPoint(c[0], c[1], c[2], c[3])

		#Cutting planes
		self.plane_x = vtk.vtkPlane()
		self.plane_x.SetOrigin(self.clip_x, 0, 0)
		self.plane_x.SetNormal(1, 0, 0)
		self.clipper_x = vtk.vtkClipPolyData()
		self.clipper_x.SetClipFunction(self.plane_x)
		self.clipper_x.SetInputConnection(self.ct_contour.GetOutputPort())

		self.plane_y = vtk.vtkPlane()
		self.plane_y.SetOrigin(0, self.clip_y, 0)
		self.plane_y.SetNormal(0, 1, 0)
		self.clipper_y = vtk.vtkClipPolyData()
		self.clipper_y.SetClipFunction(self.plane_y)
		self.clipper_y.SetInputConnection(self.clipper_x.GetOutputPort())

		self.plane_z = vtk.vtkPlane()
		self.plane_z.SetOrigin(0, 0, self.clip_z)
		self.plane_z.SetNormal(0, 0, 1)
		self.clipper_z = vtk.vtkClipPolyData()
		self.clipper_z.SetClipFunction(self.plane_z)
		self.clipper_z.SetInputConnection(self.clipper_y.GetOutputPort())

		probe_filter = vtk.vtkProbeFilter()
		probe_filter.SetSourceConnection(gm_image.GetOutputPort())
		probe_filter.SetInputConnection(self.clipper_z.GetOutputPort())

		color_mapper = vtk.vtkPolyDataMapper()
		color_mapper.SetLookupTable(color_func)
		color_mapper.SetInputConnection(probe_filter.GetOutputPort())
		color_mapper.SetScalarRange(probe_filter.GetOutput().GetScalarRange())

		colorBar = vtk.vtkScalarBarActor()
		colorBar.SetLookupTable(color_mapper.GetLookupTable())
		colorBar.SetTitle("Gradient")
		colorBar.SetNumberOfLabels(5)
		colorBar.SetLabelFormat("%4.0f")
		colorBar.SetPosition(0.9, 0.1)
		colorBar.SetWidth(0.08)
		colorBar.SetHeight(0.6)

		color_actor=vtk.vtkActor()
		#color_actor.GetProperty().SetRepresentationToWireframe()
		color_actor.SetMapper(color_mapper)

		backFaces = vtk.vtkProperty()
		backFaces.SetSpecular(0)
		backFaces.SetDiffuse(0)
		backFaces.SetAmbient(0)
		backFaces.SetAmbientColor(1,0,0)
		color_actor.SetBackfaceProperty(backFaces)
		
		ren = vtk.vtkRenderer()
		renWin = vtk.vtkRenderWindow()
		renWin.AddRenderer(ren)
		iren = vtk.vtkRenderWindowInteractor()
		iren.SetRenderWindow(renWin)

		ren.AddActor(color_actor)
		ren.AddActor(colorBar)
		ren.ResetCamera()
		ren.SetBackground(0.2,0.3,0.4)
		ren.ResetCameraClippingRange()
		renWin.SetSize(1200, 600)

		clipXSlider = vtk.vtkSliderRepresentation2D()
		clipXSlider.SetMinimumValue(0)
		clipXSlider.SetMaximumValue(300)
		clipXSlider.SetValue(self.clip_x)
		clipXSlider.SetTitleText("X")
		clipXSlider.GetPoint1Coordinate().SetCoordinateSystemToNormalizedDisplay()
		clipXSlider.GetPoint1Coordinate().SetValue(0.01, 0.3)
		clipXSlider.GetPoint2Coordinate().SetCoordinateSystemToNormalizedDisplay()
		clipXSlider.GetPoint2Coordinate().SetValue(0.2, 0.3)
		clipXSlider.SetSliderLength(0.02)
		clipXSlider.SetSliderWidth(0.03)
		clipXSlider.SetEndCapLength(0.01)
		clipXSlider.SetEndCapWidth(0.03)
		clipXSlider.SetTubeWidth(0.005)
		clipXSlider.SetLabelFormat("%1.2lf")
		clipXSlider.SetTitleHeight(0.02)
		clipXSlider.SetLabelHeight(0.02)
		SliderWidget2 = vtk.vtkSliderWidget()
		SliderWidget2.SetInteractor(iren)
		SliderWidget2.SetRepresentation(clipXSlider)
		SliderWidget2.KeyPressActivationOff()
		SliderWidget2.SetAnimationModeToAnimate()
		SliderWidget2.SetEnabled(True)
		SliderWidget2.AddObserver("EndInteractionEvent", self.clipXSliderHandler)

		clipYSlider = vtk.vtkSliderRepresentation2D()
		clipYSlider.SetMinimumValue(0)
		clipYSlider.SetMaximumValue(300)
		clipYSlider.SetValue(self.clip_y)
		clipYSlider.SetTitleText("Y")
		clipYSlider.GetPoint1Coordinate().SetCoordinateSystemToNormalizedDisplay()
		clipYSlider.GetPoint1Coordinate().SetValue(0.01, 0.2)
		clipYSlider.GetPoint2Coordinate().SetCoordinateSystemToNormalizedDisplay()
		clipYSlider.GetPoint2Coordinate().SetValue(0.2, 0.2)
		clipYSlider.SetSliderLength(0.02)
		clipYSlider.SetSliderWidth(0.03)
		clipYSlider.SetEndCapLength(0.01)
		clipYSlider.SetEndCapWidth(0.03)
		clipYSlider.SetTubeWidth(0.005)
		clipYSlider.SetLabelFormat("%1.2lf")
		clipYSlider.SetTitleHeight(0.02)
		clipYSlider.SetLabelHeight(0.02)
		SliderWidget3 = vtk.vtkSliderWidget()
		SliderWidget3.SetInteractor(iren)
		SliderWidget3.SetRepresentation(clipYSlider)
		SliderWidget3.KeyPressActivationOff()
		SliderWidget3.SetAnimationModeToAnimate()
		SliderWidget3.SetEnabled(True)
		SliderWidget3.AddObserver("EndInteractionEvent", self.clipYSliderHandler)

		clipZSlider = vtk.vtkSliderRepresentation2D()
		clipZSlider.SetMinimumValue(0)
		clipZSlider.SetMaximumValue(300)
		clipZSlider.SetValue(self.clip_z)
		clipZSlider.SetTitleText("Z")
		clipZSlider.GetPoint1Coordinate().SetCoordinateSystemToNormalizedDisplay()
		clipZSlider.GetPoint1Coordinate().SetValue(0.01, 0.1)
		clipZSlider.GetPoint2Coordinate().SetCoordinateSystemToNormalizedDisplay()
		clipZSlider.GetPoint2Coordinate().SetValue(0.2, 0.1)
		clipZSlider.SetSliderLength(0.02)
		clipZSlider.SetSliderWidth(0.03)
		clipZSlider.SetEndCapLength(0.01)
		clipZSlider.SetEndCapWidth(0.03)
		clipZSlider.SetTubeWidth(0.005)
		clipZSlider.SetLabelFormat("%1.2lf")
		clipZSlider.SetTitleHeight(0.02)
		clipZSlider.SetLabelHeight(0.02)
		SliderWidget4 = vtk.vtkSliderWidget()
		SliderWidget4.SetInteractor(iren)
		SliderWidget4.SetRepresentation(clipZSlider)
		SliderWidget4.KeyPressActivationOff()
		SliderWidget4.SetAnimationModeToAnimate()
		SliderWidget4.SetEnabled(True)
		SliderWidget4.AddObserver("EndInteractionEvent", self.clipZSliderHandler)

		# Render
		iren.Initialize()
		renWin.SetSize(1200, 800)
		renWin.SetWindowName("Project 3b: Isocontours - Pedro Acevedo & Randy Consuegra")
		renWin.Render()
		iren.Start()


def readFromFile(name):
	information = list()
	with open(name, "r") as f:
		for line in f.readlines():
			li = line.strip()
			if not li.startswith("#"):
				var = line.split()
				if(len(var) == 1):
					information.extend([int(var[0])])
				else:
					information.append([int(i) for i in var])
	return information

if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument('data', help='File with 3D scalar dataset')
	parser.add_argument('gradmag', help='File with gradient magnitude')
	parser.add_argument('isoval', help='txt with isovalues')
	parser.add_argument('--cmap', type=str, metavar='filename', help='input colormap file', default='NULL')
	parser.add_argument('--clip', type=int, metavar='int', nargs=3,
						help='initial positions of clipping planes', default=DEFAULT_PLANE_POS)
	args = parser.parse_args()

	args.isoval = readFromFile(args.isoval)

	if args.cmap != 'NULL':
		args.cmap = readFromFile(args.cmap)
	else:
		args.cmap = DEFAULT_COLORMAP

	Visualization(args = args)