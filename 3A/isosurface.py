#!/usr/bin/env python


import sys
import argparse

import vtk

# default values
DEFAULT_ISOVALUE = 500
DEFAULT_COORDINATES = [0, 0, 0]

class Visualization(object):
	def isovalue_slider_handler(self, obj, event):
		self.isovalue = obj.GetRepresentation().GetValue()
		self.contours.SetValue(0, self.isovalue)

	def clip_x_slider_handler(self, obj, event):
		self.clip_x = obj.GetRepresentation().GetValue()
		self.update_visualization()

	def clip_y_slider_handler(self, obj, event):
		self.clip_y = obj.GetRepresentation().GetValue()
		self.update_visualization()

	def clip_z_slider_handler(self, obj, event):
		self.clip_z = obj.GetRepresentation().GetValue()
		self.update_visualization()

	def update_visualization(self):
		self.plane_x.SetOrigin((self.clip_x,0,0))
		self.plane_y.SetOrigin(0,self.clip_y,0)
		self.plane_z.SetOrigin(0,0,self.clip_z)
		self.clipper_x.Update()
		self.clipper_y.Update()
		self.clipper_z.Update()

	def __init__(self, args):
		# Image loading

		self.isovalue = args.isoval
		self.clip_x = args.clip[0]
		self.clip_y = args.clip[1]
		self.clip_z = args.clip[2]

		ct_name = args.file
		ct_image = vtk.vtkXMLImageDataReader()
		ct_image.SetFileName(ct_name)
		ct_image.Update()


		r = ct_image.GetOutput().GetScalarRange()
		datamin = r[0]
		datamax = r[1]

		self.contours = vtk.vtkContourFilter()
		self.contours.SetInputConnection(ct_image.GetOutputPort());
		self.contours.ComputeNormalsOn()
		self.contours.SetValue(0, self.isovalue)

		#Cutting planes
		self.plane_x = vtk.vtkPlane()
		self.plane_x.SetOrigin(self.clip_x, 0, 0)
		self.plane_x.SetNormal(1, 0, 0)
		self.clipper_x = vtk.vtkClipPolyData()
		self.clipper_x.SetClipFunction(self.plane_x)
		self.clipper_x.SetInputConnection(self.contours.GetOutputPort())


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

		#Color map
		color_scale = vtk.vtkColorTransferFunction()
		color_scale.SetColorSpaceToRGB()
		color_scale.AddRGBPoint(1319, 0.9, 0.9, 0.9)  # bone
		color_scale.AddRGBPoint(1153, 0.9, 0.9, 0.9)  # bone
		color_scale.AddRGBPoint(1140, 204/256, 71/256, 62/256)  # muscle
		color_scale.AddRGBPoint(1040, 248/256, 10/256, 10/256)  # muscle
		color_scale.AddRGBPoint(500, 197/256, 140/256, 133/256)  # skin
		color_scale.AddRGBPoint(753, 197/256, 140/256, 133/256)  # skin

		#Color Bar
		color_bar = vtk.vtkScalarBarActor()
		#color_bar.SetOrientationToHorizontal()
		color_bar.SetLookupTable(color_scale)
		color_bar.SetTitle("Isovalues Scale")
		color_bar.SetLabelFormat("%4.0f")
		color_bar.SetPosition(0.9, 0.1)
		color_bar.SetWidth(0.1)
		color_bar.SetHeight(0.7)

		# mapper and actor
		mapper = vtk.vtkDataSetMapper()
		mapper.SetInputConnection(self.clipper_z.GetOutputPort())
		mapper.SetLookupTable(color_scale)

		actor = vtk.vtkActor()
		actor.SetMapper(mapper)

		renderer = vtk.vtkRenderer()
		render_window = vtk.vtkRenderWindow()
		render_window.AddRenderer(renderer)
		interactive_ren = vtk.vtkRenderWindowInteractor()
		interactive_ren.SetRenderWindow(render_window)

		renderer.AddActor(actor)
		renderer.AddActor(color_bar)
		renderer.ResetCamera()
		renderer.SetBackground(0.2,0.3,0.4)
		renderer.ResetCameraClippingRange()
		render_window.SetSize(1200, 600)

		isovalueSlider = vtk.vtkSliderRepresentation2D()
		isovalueSlider.SetMinimumValue(100)
		isovalueSlider.SetMaximumValue(2000)
		isovalueSlider.SetValue(self.isovalue)
		isovalueSlider.SetTitleText("Isovalue")
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
		SliderWidget1.SetInteractor(interactive_ren)
		SliderWidget1.SetRepresentation(isovalueSlider)
		SliderWidget1.KeyPressActivationOff()
		SliderWidget1.SetAnimationModeToAnimate()
		SliderWidget1.SetEnabled(True)
		SliderWidget1.AddObserver("EndInteractionEvent", self.isovalue_slider_handler)

		clipXSlider = vtk.vtkSliderRepresentation2D()
		clipXSlider.SetMinimumValue(0)
		clipXSlider.SetMaximumValue(250)
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
		SliderWidget2.SetInteractor(interactive_ren)
		SliderWidget2.SetRepresentation(clipXSlider)
		SliderWidget2.KeyPressActivationOff()
		SliderWidget2.SetAnimationModeToAnimate()
		SliderWidget2.SetEnabled(True)
		SliderWidget2.AddObserver("EndInteractionEvent", self.clip_x_slider_handler)

		clipYSlider = vtk.vtkSliderRepresentation2D()
		clipYSlider.SetMinimumValue(0)
		clipYSlider.SetMaximumValue(250)
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
		SliderWidget3.SetInteractor(interactive_ren)
		SliderWidget3.SetRepresentation(clipYSlider)
		SliderWidget3.KeyPressActivationOff()
		SliderWidget3.SetAnimationModeToAnimate()
		SliderWidget3.SetEnabled(True)
		SliderWidget3.AddObserver("EndInteractionEvent", self.clip_y_slider_handler)

		clipZSlider = vtk.vtkSliderRepresentation2D()
		clipZSlider.SetMinimumValue(0)
		clipZSlider.SetMaximumValue(250)
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
		SliderWidget4.SetInteractor(interactive_ren)
		SliderWidget4.SetRepresentation(clipZSlider)
		SliderWidget4.KeyPressActivationOff()
		SliderWidget4.SetAnimationModeToAnimate()
		SliderWidget4.SetEnabled(True)
		SliderWidget4.AddObserver("EndInteractionEvent", self.clip_z_slider_handler)

		# Render
		interactive_ren.Initialize()
		render_window.SetSize(800, 600)
		render_window.SetWindowName("Project 3a: Isocontours - Pedro Acevedo & Randy Consuegra")
		render_window.Render()
		interactive_ren.Start()


if __name__ == "__main__":

	# --define argument parser and parse arguments--
	parser = argparse.ArgumentParser(
		description="Takes CT images and shows them making use of VTK. Proyect 3 Part A")
	parser.add_argument('file')
	parser.add_argument('--isoval', '-v',type=int, metavar='int', help='Initial Isovalue', default=DEFAULT_ISOVALUE)
	parser.add_argument('--clip', type=int, metavar='int', nargs=3,
						help='Initial coordinates of cutting planes', default=DEFAULT_COORDINATES)
	args = parser.parse_args()

	Visualization(args)