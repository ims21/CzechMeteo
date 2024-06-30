from __future__ import absolute_import
#
#  Czech Meteo Viewer - Plugin E2
#
#  by ims (c) 2011-2024
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#

from Plugins.Plugin import PluginDescriptor

def main(session, **kwargs):
	from . import ui
	session.open(ui.czechMeteo)

def Plugins(path,**kwargs):
	return PluginDescriptor(name="Czech MeteoViewer", description=_("czech meteo information viewer"), where=[PluginDescriptor.WHERE_PLUGINMENU], icon = "czmeteo.png", fnc=main)
