# coding=utf-8
from __future__ import absolute_import

### (Don't forget to remove me)
# This is a basic skeleton for your plugin's __init__.py. You probably want to adjust the class name of your plugin
# as well as the plugin mixins it's subclassing from. This is really just a basic skeleton to get you started,
# defining your plugin as a template plugin, settings and asset plugin. Feel free to add or remove mixins
# as necessary.
#
# Take a look at the documentation on what other plugin mixins are available.
import gc
import os.path
import psutil
import time
import datetime
import numpy as np
import matplotlib.pyplot as plt
plt.switch_backend('Agg')
import matplotlib.image as mpimg
import re
import octoprint.plugin
import octoprint.printer

from .consts import (MESH_NUM_POINTS_X,
                     MESH_NUM_POINTS_Y,
                     MESH_FRONT_LEFT_X,
                     MESH_FRONT_LEFT_Y,
                     MESH_NUM_MEASURED_POINTS_X,
                     MESH_NUM_MEASURED_POINTS_Y,
                     sheet_left_x,
                     sheet_right_x,
                     sheet_front_y,
                     sheet_back_y,
                     mesh_delta_x,
                     mesh_delta_y)

def _get_free_mem():
	""" Returns:
		float: current pi free memory in KB
	"""
	return float(psutil.virtual_memory().free)/1024/1024

class PrusameshmapPlugin(octoprint.plugin.SettingsPlugin,
                         octoprint.plugin.AssetPlugin,
                         octoprint.plugin.TemplatePlugin,
                         octoprint.plugin.StartupPlugin,
                         octoprint.plugin.EventHandlerPlugin):

	##~~ SettingsPlugin mixin

	def get_settings_defaults(self):
		return dict(
                        do_level_gcode = 'G28 W ; home all without mesh bed level\nG80 ; mesh bed leveling\nG81 ; check mesh leveling results',
                        matplotlib_heatmap_theme = 'viridis'
		)

	##~~ AssetPlugin mixin

	def get_assets(self):
		# Define your plugin's asset files to automatically include in the
		# core UI here.
		return dict(
			js=["js/PrusaMeshMap.js"],
			css=["css/PrusaMeshMap.css"],
			less=["less/PrusaMeshMap.less"],
                        img_heatmap=["img/heatmap.png"]
		)
                
	##~~ TemplatePlugin mixin

        #def get_template_configs(self):
        #        return [
        #                dict(type="navbar", custom_bindings=False),
        #                dict(type="settings", custom_bindings=False)
        #        ]
        
        ##~~ EventHandlerPlugin mixin

        def on_event(self, event, payload):
            if event is "Connected":
                self._printer.commands("M1234")

	##~~ Softwareupdate hook

	def get_update_information(self):
		# Define the configuration for your plugin to use with the Software Update
		# Plugin here. See https://github.com/foosel/OctoPrint/wiki/Plugin:-Software-Update
		# for details.
		return dict(
			PrusaMeshMap=dict(
				displayName="Prusameshmap Plugin",
				displayVersion=self._plugin_version,

				# version check: github repository
				type="github_release",
				user="ff8jake",
				repo="OctoPrint-PrusaMeshMap",
				current=self._plugin_version,

				# update method: pip
				pip="https://github.com/ff8jake/OctoPrint-PrusaMeshMap/archive/{target_version}.zip"
			)
		)

        ##~~ GCode Received hook

        def mesh_level_check(self, comm, line, *args, **kwargs):
                if re.match(r"^(  -?\d+.\d+)+$", line):
			self.mesh_level_responses.append(line)
			self._logger.info("FOUND: " + line)
			self.mesh_level_generate()
		return line

        ##~~ Mesh Bed Level Heatmap Generation

	runs = 1
	starting_free_mem = 0

        mesh_level_responses = []
	fig = plt.figure(dpi=96, figsize=(10,8.3))
	ax = plt.gca()

	# Insert the background image (currently an image of the MK3 PEI-coated steel sheet)
	background_img = None

        def mesh_level_generate(self):

            # Accumulate response lines until we have all of them
            if len(self.mesh_level_responses) == MESH_NUM_POINTS_Y:
		if self.runs == 1:
			self.starting_free_mem = _get_free_mem()

		self._logger.info("Run {:d}, starting free mem: {:.2f} mb".format(self.runs, _get_free_mem()))

                self._logger.info("Generating heatmap")
		start_time = time.time()

                # TODO: Validate each row has MESH_NUM_POINTS_X values

                mesh_values = []

                # Parse response lines into a 2D array of floats in row-major order
                for response in self.mesh_level_responses:
                    response = re.sub(r"^[ ]+", "", response)
                    response = re.sub(r"[ ]+", ",", response)
                    mesh_values.append([float(i) for i in response.split(",")])

                # Generate a 2D array of the Z values in column-major order
                col_i = 0
                mesh_z = np.zeros(shape=(7,7))
                for col in mesh_values:
                    row_i = 0
                    for val in col:
                        mesh_z[col_i][row_i] = val
                        row_i = row_i + 1
                    col_i = col_i + 1

                # Calculate the X and Y values of the mesh bed points, in print area coordinates
                mesh_x = np.zeros(MESH_NUM_POINTS_X)
                for i in range(0, MESH_NUM_POINTS_X):
                    mesh_x[i] = MESH_FRONT_LEFT_X + mesh_delta_x*i

                mesh_y = np.zeros(MESH_NUM_POINTS_Y)
                for i in range(0, MESH_NUM_POINTS_Y):
                    mesh_y[i] = MESH_FRONT_LEFT_Y + mesh_delta_y*i

                bed_variance = round(mesh_z.max() - mesh_z.min(), 3)

                ############
                # Draw the heatmap
		plt.clf()
		if self.background_img is None:
			self.background_img = mpimg.imread(self.get_asset_folder() + '/img/mk52_steel_sheet.png')
		plt.imshow(self.background_img, extent=[sheet_left_x, sheet_right_x, sheet_front_y, sheet_back_y], interpolation="lanczos", cmap=plt.cm.get_cmap(self._settings.get(["matplotlib_heatmap_theme"])))

                # Plot all mesh points, including measured ones and the ones
                # that are bogus (calculated). Indicate the actual measured
                # points with a different marker.
                for x_i in range(0, len(mesh_x)):
                    for y_i in range(0, len(mesh_y)):
                        if ((x_i % MESH_NUM_MEASURED_POINTS_X) == 0) and ((y_i % MESH_NUM_MEASURED_POINTS_Y) == 0):
                            plt.plot(mesh_x[x_i], mesh_y[y_i], 'o', color='m')
                        else:
                            plt.plot(mesh_x[x_i], mesh_y[y_i], '.', color='k')

                # Draw the contour map. Y values are reversed to account for
                # bottom-up orientation of plot library
                contour = plt.contourf(mesh_x, mesh_y[::-1], mesh_z, alpha=.75, antialiased=True, cmap=plt.cm.get_cmap(self._settings.get(["matplotlib_heatmap_theme"])))

                # Set axis ranges (although we don't currently show these...)
                self.ax.set_xlim(left=sheet_left_x, right=sheet_right_x)
                #ax.set_xlim(left=sheet_left_x, right=sheet_right_x)
                self.ax.set_ylim(bottom=sheet_front_y, top=sheet_back_y)
                #ax.set_ylim(bottom=sheet_front_y, top=sheet_back_y)

                # Set various options about the graph image before
                # we generate it. Things like labeling the axes and
                # colorbar, and setting the X axis label/ticks to
                # the top to better match the G81 output.
                plt.title("Mesh Level: " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                plt.axis('image')
                plt.xlabel("X Axis (mm)")
                plt.ylabel("Y Axis (mm)")

                plt.colorbar(contour, label="Measured Level (mm)")
                
                plt.text(0.5, 0.43, "Total Bed Variance: " + str(bed_variance) + " (mm)", fontsize=10, horizontalalignment='center', verticalalignment='center', transform=self.ax.transAxes, bbox=dict(facecolor='#eeefff', alpha=0.5))

                # Save our graph as an image in the current directory.
                previous_ctime = int(os.path.getctime(self.get_asset_folder() + '/img/heatmap.png'))
                self.fig.savefig(self.get_asset_folder() + '/img/heatmap.png', bbox_inches="tight")
                new_ctime = int(os.path.getctime(self.get_asset_folder() + '/img/heatmap.png'))
		if new_ctime > previous_ctime:
			elapsed_time = time.time() - start_time
			self._logger.info("Heatmap updated, took {:.1f} sec".format(elapsed_time))
		else:
			self._logger.info("Heatmap creation failed")

		# Memory cleanup/garbage collection and logging
                del self.mesh_level_responses[:]
		gc.collect()

		free_mem = _get_free_mem()
		total_lost_mem = self.starting_free_mem - free_mem
		self._logger.info("Run {:d}, ending free mem: {:.2f} mb, total lost mem: {:.2f} mb, mb lost per run: {:.2f} mb".format(self.runs, free_mem, total_lost_mem, float(total_lost_mem)/self.runs))
		self.runs += 1


# If you want your plugin to be registered within OctoPrint under a different name than what you defined in setup.py
# ("OctoPrint-PluginSkeleton"), you may define that here. Same goes for the other metadata derived from setup.py that
# can be overwritten via __plugin_xyz__ control properties. See the documentation for that.
__plugin_name__ = "Prusa Mesh Leveling"

def __plugin_load__():
	global __plugin_implementation__
	__plugin_implementation__ = PrusameshmapPlugin()

	global __plugin_hooks__
	__plugin_hooks__ = {
		"octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information,
                "octoprint.comm.protocol.gcode.received": __plugin_implementation__.mesh_level_check
	}

