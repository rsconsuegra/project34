#!/usr/bin/env python

import vtk
import argparse

GRAD_MAX = 109404

class Visualization(object):
	"""docstring for Visualizatoin"""

	def isovalueSliderHandler(self, obj, event):
		self.isovalue = obj.GetRepresentation().GetValue()
		self.ct_contour.SetValue(0, self.isovalue)

	def gminSliderHandler(self, obj, event):
		self.gmin = obj.GetRepresentation().GetValue()
		if self.gmin>=self.gmax:
			self.gmin = self.gmax-1
			self.gminSlider.SetValue(self.gmin)

		self.gm_clipper_min.SetValue(self.gmin)
		self.gm_clipper_min.Update()

	def gmaxSliderHandler(self, obj, event):
		self.gmax = obj.GetRepresentation().GetValue()
		if self.gmin>=self.gmax:
			self.gmax = self.gmin+1
			self.gmaxSlider.SetValue(self.gmax)

		self.gm_clipper_max.SetValue(self.gmax)
		self.gm_clipper_max.Update()

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
		self.isovalue = args.val

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
		self.ct_contour.ComputeNormalsOn()
		self.ct_contour.SetValue(0, self.isovalue)
		self.ct_contour.SetInputConnection(ct_image.GetOutputPort());

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

		gmrange = probe_filter.GetOutput().GetScalarRange()
		self.gmin = gmrange[0]
		self.gmax = GRAD_MAX

		self.gm_clipper_min = vtk.vtkClipPolyData()
		self.gm_clipper_min.SetInputConnection(probe_filter.GetOutputPort())
		self.gm_clipper_min.InsideOutOff()
		self.gm_clipper_min.SetValue(self.gmin)

		self.gm_clipper_max = vtk.vtkClipPolyData()
		self.gm_clipper_max.SetInputConnection(self.gm_clipper_min.GetOutputPort())
		self.gm_clipper_max.InsideOutOn()
		self.gm_clipper_max.SetValue(int(self.gmax))

		colorTrans = vtk.vtkColorTransferFunction()
		colorTrans.SetColorSpaceToRGB()
		colorTrans.AddRGBPoint(0, 1, 1, 1)
		colorTrans.AddRGBPoint(2500, 1, 1, 1)
		colorTrans.AddRGBPoint(109404, 1, 0, 0)

		mapper = vtk.vtkPolyDataMapper()
		mapper.SetInputConnection(self.gm_clipper_max.GetOutputPort())
		mapper.SetLookupTable(colorTrans)

		actor = vtk.vtkActor()
		actor.GetProperty().SetRepresentationToWireframe()
		actor.SetMapper(mapper)

		colorBar = vtk.vtkScalarBarActor()
		colorBar.SetLookupTable(colorTrans)
		colorBar.SetTitle("gradient magnitude ")
		colorBar.SetNumberOfLabels(6)
		colorBar.SetLabelFormat("%4.0f")
		colorBar.SetPosition(0.9, 0.1)
		colorBar.SetWidth(0.1)
		colorBar.SetHeight(0.7)

		backFaces = vtk.vtkProperty()
		backFaces.SetSpecular(0)
		backFaces.SetDiffuse(0)
		backFaces.SetAmbient(0)
		backFaces.SetAmbientColor(1,0,0)
		actor.SetBackfaceProperty(backFaces)

		ren = vtk.vtkRenderer()
		renWin = vtk.vtkRenderWindow()
		renWin.AddRenderer(ren)
		iren = vtk.vtkRenderWindowInteractor()
		iren.SetRenderWindow(renWin)

		ren.AddActor(actor)
		ren.AddActor(colorBar)
		ren.ResetCamera()
		ren.SetBackground(0.2,0.3,0.4)
		ren.ResetCameraClippingRange()
		renWin.SetSize(1200, 600)

		self.gminSlider = vtk.vtkSliderRepresentation2D()
		self.gminSlider.SetMinimumValue(self.gmin)
		self.gminSlider.SetMaximumValue(self.gmax)
		self.gminSlider.SetValue(self.gmin)
		self.gminSlider.SetTitleText("gradmin")
		self.gminSlider.GetPoint1Coordinate().SetCoordinateSystemToNormalizedDisplay()
		self.gminSlider.GetPoint1Coordinate().SetValue(0.0, 0.6)
		self.gminSlider.GetPoint2Coordinate().SetCoordinateSystemToNormalizedDisplay()
		self.gminSlider.GetPoint2Coordinate().SetValue(0.2, 0.6)
		self.gminSlider.SetSliderLength(0.02)
		self.gminSlider.SetSliderWidth(0.03)
		self.gminSlider.SetEndCapLength(0.01)
		self.gminSlider.SetEndCapWidth(0.03)
		self.gminSlider.SetTubeWidth(0.005)
		self.gminSlider.SetLabelFormat("%3.0lf")
		self.gminSlider.SetTitleHeight(0.02)
		self.gminSlider.SetLabelHeight(0.02)
		self.gminSliderWidget = vtk.vtkSliderWidget()
		self.gminSliderWidget.SetInteractor(iren)
		self.gminSliderWidget.SetRepresentation(self.gminSlider)
		self.gminSliderWidget.KeyPressActivationOff()
		self.gminSliderWidget.SetAnimationModeToAnimate()
		self.gminSliderWidget.SetEnabled(True)
		self.gminSliderWidget.AddObserver("EndInteractionEvent", self.gminSliderHandler)

		self.gmaxSlider = vtk.vtkSliderRepresentation2D()
		self.gmaxSlider.SetMinimumValue(self.gmin)
		self.gmaxSlider.SetMaximumValue(self.gmax)
		self.gmaxSlider.SetValue(self.gmax)
		self.gmaxSlider.SetTitleText("gradmax")
		self.gmaxSlider.GetPoint1Coordinate().SetCoordinateSystemToNormalizedDisplay()
		self.gmaxSlider.GetPoint1Coordinate().SetValue(0.0, 0.5)
		self.gmaxSlider.GetPoint2Coordinate().SetCoordinateSystemToNormalizedDisplay()
		self.gmaxSlider.GetPoint2Coordinate().SetValue(0.2, 0.5)
		self.gmaxSlider.SetSliderLength(0.02)
		self.gmaxSlider.SetSliderWidth(0.03)
		self.gmaxSlider.SetEndCapLength(0.01)
		self.gmaxSlider.SetEndCapWidth(0.03)
		self.gmaxSlider.SetTubeWidth(0.005)
		self.gmaxSlider.SetLabelFormat("%3.0lf")
		self.gmaxSlider.SetTitleHeight(0.02)
		self.gmaxSlider.SetLabelHeight(0.02)
		self.gmaxSliderWidget = vtk.vtkSliderWidget()
		self.gmaxSliderWidget.SetInteractor(iren)
		self.gmaxSliderWidget.SetRepresentation(self.gmaxSlider)
		self.gmaxSliderWidget.KeyPressActivationOff()
		self.gmaxSliderWidget.SetAnimationModeToAnimate()
		self.gmaxSliderWidget.SetEnabled(True)
		self.gmaxSliderWidget.AddObserver("EndInteractionEvent", self.gmaxSliderHandler)

		isovalueSlider = vtk.vtkSliderRepresentation2D()
		isovalueSlider.SetMinimumValue(500/5)
		isovalueSlider.SetMaximumValue(1500/5)
		isovalueSlider.SetValue(self.isovalue)
		isovalueSlider.SetTitleText("isovalue")
		isovalueSlider.GetPoint1Coordinate().SetCoordinateSystemToNormalizedDisplay()
		isovalueSlider.GetPoint1Coordinate().SetValue(0.0, 0.4)
		isovalueSlider.GetPoint2Coordinate().SetCoordinateSystemToNormalizedDisplay()
		isovalueSlider.GetPoint2Coordinate().SetValue(0.2, 0.4)
		isovalueSlider.SetSliderLength(0.02)
		isovalueSlider.SetSliderWidth(0.03)
		isovalueSlider.SetEndCapLength(0.01)
		isovalueSlider.SetEndCapWidth(0.03)
		isovalueSlider.SetTubeWidth(0.005)
		isovalueSlider.SetLabelFormat("%3.0lf")
		isovalueSlider.SetTitleHeight(0.02)
		isovalueSlider.SetLabelHeight(0.02)
		SliderWidget1 = vtk.vtkSliderWidget()
		SliderWidget1.SetInteractor(iren)
		SliderWidget1.SetRepresentation(isovalueSlider)
		SliderWidget1.KeyPressActivationOff()
		SliderWidget1.SetAnimationModeToAnimate()
		SliderWidget1.SetEnabled(True)
		SliderWidget1.AddObserver("EndInteractionEvent", self.isovalueSliderHandler)

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
		renWin.SetWindowName("Project 4a: Isocontours - Pedro Acevedo & Randy Consuegra")
		renWin.Render()
		iren.Start()



if __name__ == "__main__":
	# --define argument parser and parse arguments--
	parser = argparse.ArgumentParser()
	parser.add_argument('data', help='File with 3D scalar dataset')
	parser.add_argument('gradmag', help='File with gradient magnitude')
	parser.add_argument('--val', type=int, help='Initial isovalue',
		metavar='int', default=500)
	parser.add_argument('--clip', type=int, metavar='int', nargs=3,
						help='initial positions of clipping planes', default=[0, 0, 0])
	args = parser.parse_args()

	Visualization(args = args)