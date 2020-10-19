#!/usr/bin/env python

import vtk
import argparse

GRAD_MAX = 109404

class Visualization(object):
	"""docstring for Visualizatoin"""

	def slider_isovalue_handler(self, obj, event):
		self.isovalue = obj.GetRepresentation().GetValue()
		self.ct_contour.SetValue(0, self.isovalue)

	def gmin_slider_handler(self, obj, event):
		self.gmin = obj.GetRepresentation().GetValue()
		if self.gmin>=self.gmax:
			self.gmin = self.gmax-1
			self.gmin_slider.SetValue(self.gmin)

		self.gm_clipper_min.SetValue(self.gmin)
		self.gm_clipper_min.Update()

	def gmax_slider_handler(self, obj, event):
		self.gmax = obj.GetRepresentation().GetValue()
		if self.gmin>=self.gmax:
			self.gmax = self.gmin+1
			self.gmax_slider.SetValue(self.gmax)

		self.gm_clipper_max.SetValue(self.gmax)
		self.gm_clipper_max.Update()

	def clip_x_slider_handler(self,obj, event):
		self.clip_x = obj.GetRepresentation().GetValue()
		self.updateCT()

	def clip_y_slider_handler(self,obj, event):
		self.clip_y = obj.GetRepresentation().GetValue()
		self.updateCT()

	def clip_z_slider_handler(self,obj, event):
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
		probe_filter.SetInputConnection(1,gm_image.GetOutputPort())
		probe_filter.SetInputConnection(0,self.clipper_z.GetOutputPort())

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

		color_transfer_func = vtk.vtkColorTransferFunction()
		color_transfer_func.SetColorSpaceToRGB()
		color_transfer_func.AddRGBPoint(0, 1, 1, 1)
		color_transfer_func.AddRGBPoint(2500, 1, 1, 1)
		color_transfer_func.AddRGBPoint(109404, 1, 0, 0)

		mapper = vtk.vtkPolyDataMapper()
		mapper.SetInputConnection(self.gm_clipper_max.GetOutputPort())
		mapper.SetLookupTable(color_transfer_func)

		actor = vtk.vtkActor()
		actor.SetMapper(mapper)

		color_bar = vtk.vtkScalarBarActor()
		color_bar.SetLookupTable(color_transfer_func)
		color_bar.SetTitle("gradient magnitude ")
		color_bar.SetNumberOfLabels(6)
		color_bar.SetLabelFormat("%4.0f")
		color_bar.SetPosition(0.9, 0.1)
		color_bar.SetWidth(0.1)
		color_bar.SetHeight(0.7)

		back_faces = vtk.vtkProperty()
		back_faces.SetSpecular(0)
		back_faces.SetDiffuse(0)
		back_faces.SetAmbient(0)
		back_faces.SetAmbientColor(1,0,0)
		actor.SetBackfaceProperty(back_faces)

		renderer = vtk.vtkRenderer()
		render_window = vtk.vtkRenderWindow()
		render_window.AddRenderer(renderer)
		interactive_render = vtk.vtkRenderWindowInteractor()
		interactive_render.SetRenderWindow(render_window)

		renderer.AddActor(actor)
		renderer.AddActor(color_bar)
		renderer.ResetCamera()
		renderer.SetBackground(0.2,0.3,0.4)
		renderer.ResetCameraClippingRange()
		render_window.SetSize(1200, 600)

		self.gmin_slider = vtk.vtkSliderRepresentation2D()
		self.gmin_slider.SetMinimumValue(self.gmin)
		self.gmin_slider.SetMaximumValue(self.gmax)
		self.gmin_slider.SetValue(self.gmin)
		self.gmin_slider.SetTitleText("gradmin")
		self.gmin_slider.GetPoint1Coordinate().SetCoordinateSystemToNormalizedDisplay()
		self.gmin_slider.GetPoint1Coordinate().SetValue(0.01, 0.6)
		self.gmin_slider.GetPoint2Coordinate().SetCoordinateSystemToNormalizedDisplay()
		self.gmin_slider.GetPoint2Coordinate().SetValue(0.2, 0.6)
		self.gmin_slider.SetSliderLength(0.02)
		self.gmin_slider.SetSliderWidth(0.03)
		self.gmin_slider.SetEndCapLength(0.01)
		self.gmin_slider.SetEndCapWidth(0.03)
		self.gmin_slider.SetTubeWidth(0.005)
		self.gmin_slider.SetLabelFormat("%3.0lf")
		self.gmin_slider.SetTitleHeight(0.02)
		self.gmin_slider.SetLabelHeight(0.02)
		self.gmin_slider_widget = vtk.vtkSliderWidget()
		self.gmin_slider_widget.SetInteractor(interactive_render)
		self.gmin_slider_widget.SetRepresentation(self.gmin_slider)
		self.gmin_slider_widget.KeyPressActivationOff()
		self.gmin_slider_widget.SetAnimationModeToAnimate()
		self.gmin_slider_widget.SetEnabled(True)
		self.gmin_slider_widget.AddObserver("EndInteractionEvent", self.gmin_slider_handler)

		self.gmax_slider = vtk.vtkSliderRepresentation2D()
		self.gmax_slider.SetMinimumValue(self.gmin)
		self.gmax_slider.SetMaximumValue(200000)
		self.gmax_slider.SetValue(self.gmax)
		self.gmax_slider.SetTitleText("gradmax")
		self.gmax_slider.GetPoint1Coordinate().SetCoordinateSystemToNormalizedDisplay()
		self.gmax_slider.GetPoint1Coordinate().SetValue(0.01, 0.5)
		self.gmax_slider.GetPoint2Coordinate().SetCoordinateSystemToNormalizedDisplay()
		self.gmax_slider.GetPoint2Coordinate().SetValue(0.2, 0.5)
		self.gmax_slider.SetSliderLength(0.02)
		self.gmax_slider.SetSliderWidth(0.03)
		self.gmax_slider.SetEndCapLength(0.01)
		self.gmax_slider.SetEndCapWidth(0.03)
		self.gmax_slider.SetTubeWidth(0.005)
		self.gmax_slider.SetLabelFormat("%3.0lf")
		self.gmax_slider.SetTitleHeight(0.02)
		self.gmax_slider.SetLabelHeight(0.02)
		self.gmax_slider_widget = vtk.vtkSliderWidget()
		self.gmax_slider_widget.SetInteractor(interactive_render)
		self.gmax_slider_widget.SetRepresentation(self.gmax_slider)
		self.gmax_slider_widget.KeyPressActivationOff()
		self.gmax_slider_widget.SetAnimationModeToAnimate()
		self.gmax_slider_widget.SetEnabled(True)
		self.gmax_slider_widget.AddObserver("EndInteractionEvent", self.gmax_slider_handler)

		slider_isovalue = vtk.vtkSliderRepresentation2D()
		slider_isovalue.SetMinimumValue(500/5)
		slider_isovalue.SetMaximumValue(3000)
		slider_isovalue.SetValue(self.isovalue)
		slider_isovalue.SetTitleText("isovalue")
		slider_isovalue.GetPoint1Coordinate().SetCoordinateSystemToNormalizedDisplay()
		slider_isovalue.GetPoint1Coordinate().SetValue(0.01, 0.4)
		slider_isovalue.GetPoint2Coordinate().SetCoordinateSystemToNormalizedDisplay()
		slider_isovalue.GetPoint2Coordinate().SetValue(0.2, 0.4)
		slider_isovalue.SetSliderLength(0.02)
		slider_isovalue.SetSliderWidth(0.03)
		slider_isovalue.SetEndCapLength(0.01)
		slider_isovalue.SetEndCapWidth(0.03)
		slider_isovalue.SetTubeWidth(0.005)
		slider_isovalue.SetLabelFormat("%3.0lf")
		slider_isovalue.SetTitleHeight(0.02)
		slider_isovalue.SetLabelHeight(0.02)
		slider_widget_isovalue = vtk.vtkSliderWidget()
		slider_widget_isovalue.SetInteractor(interactive_render)
		slider_widget_isovalue.SetRepresentation(slider_isovalue)
		slider_widget_isovalue.KeyPressActivationOff()
		slider_widget_isovalue.SetAnimationModeToAnimate()
		slider_widget_isovalue.SetEnabled(True)
		slider_widget_isovalue.AddObserver("EndInteractionEvent", self.slider_isovalue_handler)

		slider_clip_x = vtk.vtkSliderRepresentation2D()
		slider_clip_x.SetMinimumValue(0)
		slider_clip_x.SetMaximumValue(300)
		slider_clip_x.SetValue(self.clip_x)
		slider_clip_x.SetTitleText("X")
		slider_clip_x.GetPoint1Coordinate().SetCoordinateSystemToNormalizedDisplay()
		slider_clip_x.GetPoint1Coordinate().SetValue(0.01, 0.3)
		slider_clip_x.GetPoint2Coordinate().SetCoordinateSystemToNormalizedDisplay()
		slider_clip_x.GetPoint2Coordinate().SetValue(0.2, 0.3)
		slider_clip_x.SetSliderLength(0.02)
		slider_clip_x.SetSliderWidth(0.03)
		slider_clip_x.SetEndCapLength(0.01)
		slider_clip_x.SetEndCapWidth(0.03)
		slider_clip_x.SetTubeWidth(0.005)
		slider_clip_x.SetLabelFormat("%1.2lf")
		slider_clip_x.SetTitleHeight(0.02)
		slider_clip_x.SetLabelHeight(0.02)
		Slider_widget_x = vtk.vtkSliderWidget()
		Slider_widget_x.SetInteractor(interactive_render)
		Slider_widget_x.SetRepresentation(slider_clip_x)
		Slider_widget_x.KeyPressActivationOff()
		Slider_widget_x.SetAnimationModeToAnimate()
		Slider_widget_x.SetEnabled(True)
		Slider_widget_x.AddObserver("EndInteractionEvent", self.clip_x_slider_handler)

		slider_clip_y = vtk.vtkSliderRepresentation2D()
		slider_clip_y.SetMinimumValue(0)
		slider_clip_y.SetMaximumValue(300)
		slider_clip_y.SetValue(self.clip_y)
		slider_clip_y.SetTitleText("Y")
		slider_clip_y.GetPoint1Coordinate().SetCoordinateSystemToNormalizedDisplay()
		slider_clip_y.GetPoint1Coordinate().SetValue(0.01, 0.2)
		slider_clip_y.GetPoint2Coordinate().SetCoordinateSystemToNormalizedDisplay()
		slider_clip_y.GetPoint2Coordinate().SetValue(0.2, 0.2)
		slider_clip_y.SetSliderLength(0.02)
		slider_clip_y.SetSliderWidth(0.03)
		slider_clip_y.SetEndCapLength(0.01)
		slider_clip_y.SetEndCapWidth(0.03)
		slider_clip_y.SetTubeWidth(0.005)
		slider_clip_y.SetLabelFormat("%1.2lf")
		slider_clip_y.SetTitleHeight(0.02)
		slider_clip_y.SetLabelHeight(0.02)
		slider_widget_y = vtk.vtkSliderWidget()
		slider_widget_y.SetInteractor(interactive_render)
		slider_widget_y.SetRepresentation(slider_clip_y)
		slider_widget_y.KeyPressActivationOff()
		slider_widget_y.SetAnimationModeToAnimate()
		slider_widget_y.SetEnabled(True)
		slider_widget_y.AddObserver("EndInteractionEvent", self.clip_y_slider_handler)

		clip_z_slider = vtk.vtkSliderRepresentation2D()
		clip_z_slider.SetMinimumValue(0)
		clip_z_slider.SetMaximumValue(300)
		clip_z_slider.SetValue(self.clip_z)
		clip_z_slider.SetTitleText("Z")
		clip_z_slider.GetPoint1Coordinate().SetCoordinateSystemToNormalizedDisplay()
		clip_z_slider.GetPoint1Coordinate().SetValue(0.01, 0.1)
		clip_z_slider.GetPoint2Coordinate().SetCoordinateSystemToNormalizedDisplay()
		clip_z_slider.GetPoint2Coordinate().SetValue(0.2, 0.1)
		clip_z_slider.SetSliderLength(0.02)
		clip_z_slider.SetSliderWidth(0.03)
		clip_z_slider.SetEndCapLength(0.01)
		clip_z_slider.SetEndCapWidth(0.03)
		clip_z_slider.SetTubeWidth(0.005)
		clip_z_slider.SetLabelFormat("%1.2lf")
		clip_z_slider.SetTitleHeight(0.02)
		clip_z_slider.SetLabelHeight(0.02)
		Slider_widget_z = vtk.vtkSliderWidget()
		Slider_widget_z.SetInteractor(interactive_render)
		Slider_widget_z.SetRepresentation(clip_z_slider)
		Slider_widget_z.KeyPressActivationOff()
		Slider_widget_z.SetAnimationModeToAnimate()
		Slider_widget_z.SetEnabled(True)
		Slider_widget_z.AddObserver("EndInteractionEvent", self.clip_z_slider_handler)

		# Render
		interactive_render.Initialize()
		render_window.SetSize(800, 400)
		render_window.SetWindowName("Project 4a: Isocontours - Pedro Acevedo & Randy Consuegra")
		render_window.Render()
		interactive_render.Start()


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