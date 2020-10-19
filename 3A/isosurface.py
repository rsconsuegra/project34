#!/usr/bin/env python

import argparse
import sys

import vtk

# default values
DEFAULT_ISOVALUE = 500
DEFAULT_COORDINATES = [0, 0, 0]

class Visualization(object):
	def slider_isovalue_handler(self, obj, event):
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

		ct_name = args.data
		ct_image = vtk.vtkXMLImageDataReader()
		ct_image.SetFileName(ct_name)
		ct_image.Update()

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
		color_scale.AddRGBPoint(1319, 0.9, 0.9, 0.9)
		color_scale.AddRGBPoint(1153, 0.9, 0.9, 0.9)
		color_scale.AddRGBPoint(1140, 192/256, 104/256, 88/256)  # muscle
		color_scale.AddRGBPoint(1040, 248/256, 10/256, 10/256)  # muscle
		color_scale.AddRGBPoint(500, 177/256, 122/256, 101/256)  # skin
		color_scale.AddRGBPoint(753, 197/256, 140/256, 133/256)  # skin

		#Color Bar
		color_bar = vtk.vtkScalarBarActor()
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

		slider_isovalue = vtk.vtkSliderRepresentation2D()
		slider_isovalue.SetMinimumValue(100)
		slider_isovalue.SetMaximumValue(2000)
		slider_isovalue.SetValue(self.isovalue)
		slider_isovalue.SetTitleText("Isovalue")
		slider_isovalue.GetPoint1Coordinate().SetCoordinateSystemToNormalizedDisplay()
		slider_isovalue.GetPoint1Coordinate().SetValue(0.01, 0.4)
		slider_isovalue.GetPoint2Coordinate().SetCoordinateSystemToNormalizedDisplay()
		slider_isovalue.GetPoint2Coordinate().SetValue(0.2, 0.4)
		slider_isovalue.SetSliderLength(0.01)
		slider_isovalue.SetSliderWidth(0.03)
		slider_isovalue.SetEndCapLength(0.01)
		slider_isovalue.SetEndCapWidth(0.03)
		slider_isovalue.SetTubeWidth(0.005)
		slider_isovalue.SetLabelFormat("%3.0lf")
		slider_isovalue.SetTitleHeight(0.02)
		slider_isovalue.SetLabelHeight(0.02)
		slider_widget_isovalues = vtk.vtkSliderWidget()
		slider_widget_isovalues.SetInteractor(interactive_ren)
		slider_widget_isovalues.SetRepresentation(slider_isovalue)
		slider_widget_isovalues.KeyPressActivationOff()
		slider_widget_isovalues.SetAnimationModeToAnimate()
		slider_widget_isovalues.SetEnabled(True)
		slider_widget_isovalues.AddObserver("EndInteractionEvent", self.slider_isovalue_handler)

		slider_clip_x = vtk.vtkSliderRepresentation2D()
		slider_clip_x.SetMinimumValue(0)
		slider_clip_x.SetMaximumValue(190)
		slider_clip_x.SetValue(self.clip_x)
		slider_clip_x.SetTitleText("X")
		slider_clip_x.GetPoint1Coordinate().SetCoordinateSystemToNormalizedDisplay()
		slider_clip_x.GetPoint1Coordinate().SetValue(0.01, 0.3)
		slider_clip_x.GetPoint2Coordinate().SetCoordinateSystemToNormalizedDisplay()
		slider_clip_x.GetPoint2Coordinate().SetValue(0.2, 0.3)
		slider_clip_x.SetSliderLength(0.01)
		slider_clip_x.SetSliderWidth(0.03)
		slider_clip_x.SetEndCapLength(0.01)
		slider_clip_x.SetEndCapWidth(0.03)
		slider_clip_x.SetTubeWidth(0.005)
		slider_clip_x.SetLabelFormat("%1.2lf")
		slider_clip_x.SetTitleHeight(0.02)
		slider_clip_x.SetLabelHeight(0.02)
		slider_widget_x = vtk.vtkSliderWidget()
		slider_widget_x.SetInteractor(interactive_ren)
		slider_widget_x.SetRepresentation(slider_clip_x)
		slider_widget_x.KeyPressActivationOff()
		slider_widget_x.SetAnimationModeToAnimate()
		slider_widget_x.SetEnabled(True)
		slider_widget_x.AddObserver("EndInteractionEvent", self.clip_x_slider_handler)

		slider_clip_y = vtk.vtkSliderRepresentation2D()
		slider_clip_y.SetMinimumValue(0)
		slider_clip_y.SetMaximumValue(190)
		slider_clip_y.SetValue(self.clip_y)
		slider_clip_y.SetTitleText("Y")
		slider_clip_y.GetPoint1Coordinate().SetCoordinateSystemToNormalizedDisplay()
		slider_clip_y.GetPoint1Coordinate().SetValue(0.01, 0.2)
		slider_clip_y.GetPoint2Coordinate().SetCoordinateSystemToNormalizedDisplay()
		slider_clip_y.GetPoint2Coordinate().SetValue(0.2, 0.2)
		slider_clip_y.SetSliderLength(0.01)
		slider_clip_y.SetSliderWidth(0.03)
		slider_clip_y.SetEndCapLength(0.01)
		slider_clip_y.SetEndCapWidth(0.03)
		slider_clip_y.SetTubeWidth(0.005)
		slider_clip_y.SetLabelFormat("%1.2lf")
		slider_clip_y.SetTitleHeight(0.02)
		slider_clip_y.SetLabelHeight(0.02)
		slider_widget_y = vtk.vtkSliderWidget()
		slider_widget_y.SetInteractor(interactive_ren)
		slider_widget_y.SetRepresentation(slider_clip_y)
		slider_widget_y.KeyPressActivationOff()
		slider_widget_y.SetAnimationModeToAnimate()
		slider_widget_y.SetEnabled(True)
		slider_widget_y.AddObserver("EndInteractionEvent", self.clip_y_slider_handler)

		slider_clip_z = vtk.vtkSliderRepresentation2D()
		slider_clip_z.SetMinimumValue(0)
		slider_clip_z.SetMaximumValue(190)
		slider_clip_z.SetValue(self.clip_z)
		slider_clip_z.SetTitleText("Z")
		slider_clip_z.GetPoint1Coordinate().SetCoordinateSystemToNormalizedDisplay()
		slider_clip_z.GetPoint1Coordinate().SetValue(0.01, 0.1)
		slider_clip_z.GetPoint2Coordinate().SetCoordinateSystemToNormalizedDisplay()
		slider_clip_z.GetPoint2Coordinate().SetValue(0.2, 0.1)
		slider_clip_z.SetSliderLength(0.01)
		slider_clip_z.SetSliderWidth(0.03)
		slider_clip_z.SetEndCapLength(0.01)
		slider_clip_z.SetEndCapWidth(0.03)
		slider_clip_z.SetTubeWidth(0.005)
		slider_clip_z.SetLabelFormat("%1.2lf")
		slider_clip_z.SetTitleHeight(0.02)
		slider_clip_z.SetLabelHeight(0.02)
		slider_widget_z = vtk.vtkSliderWidget()
		slider_widget_z.SetInteractor(interactive_ren)
		slider_widget_z.SetRepresentation(slider_clip_z)
		slider_widget_z.KeyPressActivationOff()
		slider_widget_z.SetAnimationModeToAnimate()
		slider_widget_z.SetEnabled(True)
		slider_widget_z.AddObserver("EndInteractionEvent", self.clip_z_slider_handler)

		# Render
		interactive_ren.Initialize()
		render_window.SetSize(800, 600)
		render_window.SetWindowName("Project 3a: Isocontours - Pedro Acevedo & Randy Consuegra")
		render_window.Render()
		interactive_ren.Start()


if __name__ == "__main__":
	#To do documentation, TAP library must be used.
	parser = argparse.ArgumentParser(
		description="Takes CT images and shows them making use of VTK. Proyect 3 Part A")
	parser.add_argument('data', help='Filename containg data to be visualized')
	parser.add_argument('--isoval', '-v',type=int, metavar='int', help='Initial Isovalue', default=DEFAULT_ISOVALUE)
	parser.add_argument('--clip', '-c', type=int, metavar='int', nargs=3,
						help='Initial coordinates of cutting planes', default=DEFAULT_COORDINATES)
	args = parser.parse_args()

	Visualization(args)