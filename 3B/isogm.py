#!/usr/bin/env python

import vtk
import argparse


DEFAULT_COLORMAP = [[0, 1, 1, 1], [2500, 1, 1, 1], [109404, 1, 0, 0]]
DEFAULT_PLANE_POS = [0, 0, 0]


class Visualization(object):
	"""docstring for Visualization"""

	def clip_x_slider_handler(self,obj, event):
		self.clip_x = obj.GetRepresentation().GetValue()
		self.update_CT()

	def clip_y_slider_handler(self,obj, event):
		self.clip_y = obj.GetRepresentation().GetValue()
		self.update_CT()

	def clip_z_slider_handler(self,obj, event):
		self.clip_z = obj.GetRepresentation().GetValue()
		self.update_CT()

	def update_CT(self):
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

		color_bar = vtk.vtkScalarBarActor()
		color_bar.SetLookupTable(color_mapper.GetLookupTable())
		color_bar.SetTitle("Gradient")
		color_bar.SetNumberOfLabels(5)
		color_bar.SetLabelFormat("%3.0f")
		color_bar.SetPosition(0.9, 0.1)
		color_bar.SetWidth(0.08)
		color_bar.SetHeight(0.6)

		color_actor=vtk.vtkActor()
		#color_actor.GetProperty().SetRepresentationToWireframe()
		color_actor.SetMapper(color_mapper)

		back_faces = vtk.vtkProperty()
		back_faces.SetSpecular(0)
		back_faces.SetDiffuse(0)
		back_faces.SetAmbient(0)
		back_faces.SetAmbientColor(1,0,0)
		color_actor.SetBackfaceProperty(back_faces)

		renderer = vtk.vtkRenderer()
		render_window = vtk.vtkRenderWindow()
		render_window.AddRenderer(renderer)
		interactive_renderer = vtk.vtkRenderWindowInteractor()
		interactive_renderer.SetRenderWindow(render_window)

		renderer.AddActor(color_actor)
		renderer.AddActor(color_bar)
		renderer.ResetCamera()
		renderer.SetBackground(0.2,0.3,0.4)
		renderer.ResetCameraClippingRange()

		slider_clip_x = vtk.vtkSliderRepresentation2D()
		slider_clip_x.SetMinimumValue(0)
		slider_clip_x.SetMaximumValue(245)
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
		slider_widget_x = vtk.vtkSliderWidget()
		slider_widget_x.SetInteractor(interactive_renderer)
		slider_widget_x.SetRepresentation(slider_clip_x)
		slider_widget_x.KeyPressActivationOff()
		slider_widget_x.SetAnimationModeToAnimate()
		slider_widget_x.SetEnabled(True)
		slider_widget_x.AddObserver("EndInteractionEvent", self.clip_x_slider_handler)

		slider_clip_y = vtk.vtkSliderRepresentation2D()
		slider_clip_y.SetMinimumValue(0)
		slider_clip_y.SetMaximumValue(245)
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
		slider_widget_y.SetInteractor(interactive_renderer)
		slider_widget_y.SetRepresentation(slider_clip_y)
		slider_widget_y.KeyPressActivationOff()
		slider_widget_y.SetAnimationModeToAnimate()
		slider_widget_y.SetEnabled(True)
		slider_widget_y.AddObserver("EndInteractionEvent", self.clip_y_slider_handler)

		slider_clip_z = vtk.vtkSliderRepresentation2D()
		slider_clip_z.SetMinimumValue(0)
		slider_clip_z.SetMaximumValue(245)
		slider_clip_z.SetValue(self.clip_z)
		slider_clip_z.SetTitleText("Z")
		slider_clip_z.GetPoint1Coordinate().SetCoordinateSystemToNormalizedDisplay()
		slider_clip_z.GetPoint1Coordinate().SetValue(0.01, 0.1)
		slider_clip_z.GetPoint2Coordinate().SetCoordinateSystemToNormalizedDisplay()
		slider_clip_z.GetPoint2Coordinate().SetValue(0.2, 0.1)
		slider_clip_z.SetSliderLength(0.02)
		slider_clip_z.SetSliderWidth(0.03)
		slider_clip_z.SetEndCapLength(0.01)
		slider_clip_z.SetEndCapWidth(0.03)
		slider_clip_z.SetTubeWidth(0.005)
		slider_clip_z.SetLabelFormat("%1.2lf")
		slider_clip_z.SetTitleHeight(0.02)
		slider_clip_z.SetLabelHeight(0.02)
		slider_widget_z = vtk.vtkSliderWidget()
		slider_widget_z.SetInteractor(interactive_renderer)
		slider_widget_z.SetRepresentation(slider_clip_z)
		slider_widget_z.KeyPressActivationOff()
		slider_widget_z.SetAnimationModeToAnimate()
		slider_widget_z.SetEnabled(True)
		slider_widget_z.AddObserver("EndInteractionEvent", self.clip_z_slider_handler)

		# Render
		interactive_renderer.Initialize()
		render_window.SetSize(800, 600)
		render_window.SetWindowName("Project 3b: Isocontours - Pedro Acevedo & Randy Consuegra")
		render_window.Render()
		interactive_renderer.Start()


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
					information.append([float(i) for i in var])
	return information

if __name__ == "__main__":
	parser = argparse.ArgumentParser(
		description="Takes CT images and shows them making use of VTK. Proyect 3 Part B")
	parser.add_argument('data', help='File with 3D scalar dataset')
	parser.add_argument('gradmag', help='File with gradient magnitude')
	parser.add_argument('isoval', help='txt with isovalues')
	parser.add_argument('--cmap','-cm', type=str, metavar='filename', help='input colormap file', default='NULL')
	parser.add_argument('--clip','-c', type=int, metavar='int', nargs=3,
						help='initial positions of clipping planes', default=DEFAULT_PLANE_POS)
	args = parser.parse_args()

	try:
		args.isoval = readFromFile(args.isoval)
	except Exception as e:
		raise Exception("Isovalues file can't be find. Check the Path or filename")


	if args.cmap != 'NULL':
		args.cmap = readFromFile(args.cmap)
	else:
		args.cmap = DEFAULT_COLORMAP

	Visualization(args = args)