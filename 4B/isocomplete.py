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
		
		for i in range(len(self.clipper_X)):
			self.clipper_X[i].Update()
			self.clipper_Y[i].Update()
			self.clipper_Z[i].Update()

	def contours(self, i, ct_image, isovalue, cmap):
		contour = vtk.vtkContourFilter()
		contour.SetInputConnection(self.ct_image.GetOutputPort());
		contour.ComputeNormalsOn()

		contour.SetValue(0, isovalue)

		color_fun = vtk.vtkColorTransferFunction()
		color_fun.SetColorSpaceToRGB()
		color_fun.AddRGBPoint(isovalue, cmap[0], cmap[1],cmap[2])

		
		clipper_x = vtk.vtkClipPolyData()
		clipper_x.SetClipFunction(self.plane_x)
		clipper_x.SetInputConnection(contour.GetOutputPort())

		clipper_y = vtk.vtkClipPolyData()
		clipper_y.SetClipFunction(self.plane_y)
		clipper_y.SetInputConnection(clipper_x.GetOutputPort())

		clipper_z = vtk.vtkClipPolyData()
		clipper_z.SetClipFunction(self.plane_z)
		clipper_z.SetInputConnection(clipper_y.GetOutputPort())

		probe_filter = vtk.vtkProbeFilter()
		probe_filter.SetSourceConnection(self.gm_image.GetOutputPort())
		probe_filter.SetInputConnection(clipper_z.GetOutputPort())

		gmin = self.gimin[i]
		gmax = self.gimax[i]

		gm_clipper_min = vtk.vtkClipPolyData()
		gm_clipper_min.SetInputConnection(probe_filter.GetOutputPort())
		gm_clipper_min.InsideOutOff()
		gm_clipper_min.SetValue(gmin)

		gm_clipper_max = vtk.vtkClipPolyData()
		gm_clipper_max.SetInputConnection(gm_clipper_min.GetOutputPort())
		gm_clipper_max.InsideOutOn()
		gm_clipper_max.SetValue(int(gmax))
		
		color_mapper = vtk.vtkPolyDataMapper()
		color_mapper.SetLookupTable(color_fun)
		color_mapper.SetInputConnection(gm_clipper_max.GetOutputPort())
		color_mapper.SetScalarRange(gm_clipper_max.GetOutput().GetScalarRange())

		color_actor=vtk.vtkActor()
		color_actor.GetProperty().SetOpacity(cmap[3])
		color_actor.SetMapper(color_mapper)

		self.clipper_X.append(clipper_x)
		self.clipper_Y.append(clipper_x)
		self.clipper_Z.append(clipper_x)

		return color_actor


	def __init__(self, args):
		## Files reading and settings
		self.isovalues = args.isoval
		self.cmap = args.cmap

		self.clip_x = args.clip[0]
		self.clip_y = args.clip[1]
		self.clip_z = args.clip[2]

		self.clipper_X = []
		self.clipper_Y = []
		self.clipper_Z = []

		self.ct_image = vtk.vtkXMLImageDataReader()
		self.ct_image.SetFileName(args.data)
		self.ct_image.Update()

		self.gm_image = vtk.vtkXMLImageDataReader()
		self.gm_image.SetFileName(args.maggrad)
		self.gm_image.Update()

		self.gimin = args.mingrad
		self.gimax = args.maxgrad

		#Cutting planes
		self.plane_x = vtk.vtkPlane()
		self.plane_x.SetOrigin(self.clip_x, 0, 0)
		self.plane_x.SetNormal(1, 0, 0)

		self.plane_y = vtk.vtkPlane()
		self.plane_y.SetOrigin(0, self.clip_y, 0)
		self.plane_y.SetNormal(0, 1, 0)

		self.plane_z = vtk.vtkPlane()
		self.plane_z.SetOrigin(0, 0, self.clip_z)
		self.plane_z.SetNormal(0, 0, 1)

		ren = vtk.vtkRenderer()
		renWin = vtk.vtkRenderWindow()
		renWin.AddRenderer(ren)
		iren = vtk.vtkRenderWindowInteractor()
		iren.SetRenderWindow(renWin)

		for i in range(len(self.isovalues)):
			ren.AddActor(self.contours(i,self.ct_image,self.isovalues[i], self.cmap[i]))

		ren.ResetCamera()
		ren.SetBackground(0.2,0.3,0.4)
		ren.ResetCameraClippingRange()
		ren.SetUseDepthPeeling(1)
		ren.SetMaximumNumberOfPeels(100)
		ren.SetOcclusionRatio(0.4)
		ren.ResetCamera()
		renWin.SetSize(1200, 600)

		clipXSlider = vtk.vtkSliderRepresentation2D()
		clipXSlider.SetMinimumValue(0)
		clipXSlider.SetMaximumValue(300)
		clipXSlider.SetValue(self.clip_x)
		clipXSlider.SetTitleText("X")
		clipXSlider.GetPoint1Coordinate().SetCoordinateSystemToNormalizedDisplay()
		clipXSlider.GetPoint1Coordinate().SetValue(0.0, 0.3)
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
		clipYSlider.GetPoint1Coordinate().SetValue(0.0, 0.2)
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
		clipZSlider.GetPoint1Coordinate().SetValue(0.0, 0.1)
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
		renWin.SetSize(800, 600)
		renWin.SetWindowName("Project 4b: Isocontours - Pedro Acevedo & Randy Consuegra")
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
					information.append([int(i) if not '.' in i else float(i) for i in var])
	return information

if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument('data', help='File with 3D scalar dataset')
	parser.add_argument('maggrad', help='File with gradient magnitude')
	parser.add_argument('params', help='txt with isovalues, grad range and scale colors.')
	parser.add_argument('--clip', type=int, metavar='int', nargs=3,
						help='initial positions of clipping planes', default=DEFAULT_PLANE_POS)
	args = parser.parse_args()

	if args.params != 'NULL':
		params = readFromFile(args.params)
		args.isoval = [param[0] for param in params]
		args.mingrad = [param[1] for param in params]
		args.maxgrad =  [param[2] for param in params]
		args.cmap = [param[3:] for param in params]
	else:
		args.params = DEFAULT_COLORMAP

	Visualization(args = args)