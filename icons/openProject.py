# Copyright 2009 Gabriel Black
#
# This file is part of Directory Maker.
#
#    Directory Maker is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    any later version.
#
#    Directory MAker is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Directory Maker.  If not, see <http://www.gnu.org/licenses/>.
from wx.lib.embeddedimage import PyEmbeddedImage

openProject = PyEmbeddedImage(
    "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"
    "SUVORK5CYII=")
getopenProjectData = openProject.GetData
getopenProjectImage = openProject.GetImage
getopenProjectBitmap = openProject.GetBitmap

