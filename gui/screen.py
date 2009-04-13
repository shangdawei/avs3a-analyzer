import gtk, gobject, cairo
from gtk import gdk
import pycha.line, pycha.bar
import random, threading, time
import serial

# Graphic plotter based on pycha
# Copyright (C) 2009 Naranjo Manuel Francisco <manuel@aircable.net>
# Copyright (C) 2009 Rassia Martin
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#


def redraw_canvas(self):
    #print getattr(self, 'window', None)
    if getattr(self, 'window', None) is not None:
	alloc = self.get_allocation()
	rect = gdk.Rectangle(alloc.x, alloc.y, alloc.width, alloc.height)
	self.window.invalidate_rect(rect, True)
	self.window.process_updates(True)
    return type(self.port) == serial.Serial # make sure we update once each second

# Handle the expose-event by drawing
def expose(self, widget, event):
    if getattr(self, 'window', None) is None:
	#print "no window on expose"
        return True

    self.draw(event, *self.window.get_size())
    return False

def on_configure_event(self, event, *args):
    if type(self.port) == file:
	self.port.seek(0)

def addReading(self, byte, pos, val):
    for i in range(0,self.LINES):
	v = int( (byte & 2**i)>0 )
	val[i] += ( (pos, v+i*2 ), )	

buffer = ""

def getDat(self):
    if self.port is None:
	#print "No data"
	return None
    
    if type(self.port) == file:
#	if getattr(self, 'min_sample', None) is not None or \
#	    getattr(self, 'max_sample', None) is not None or \
#	    self.port.tell() == 0:
	if self.port.tell() == 0:
	    self.data = self.port.read()
	    #print "File data: %s bytes long" % len(self.data)
	    return self.data
	
	return None; # no data update
    if type(self.port) == str:
	return self.port # this is the case after stop record has been pressed
    else:
	global buffer
	print self.port.inWaiting()
	buffer += self.port.read(self.port.inWaiting())
	
	if len(buffer) < 3900:
	    #print time.time(), len(buffer)
	    return None
	print len(buffer)
	
	self.data += buffer
	d = buffer
	buffer = ""
	return d

def updateInternalData(self, width, height):
    #global data
    dat = self.getDat()
    if dat is not None:
	val = list()
	samples = len(dat)
	
	for i in range(0, self.LINES):
	    val.append( tuple() ) # we have self.LINES
	
	self.addReading(ord(dat[0]), 0, val)
    
	A = dat[0]
    
	for i in range(1, len(dat)-1):
	    if dat[i] != A: # don't duplicate points
		self.addReading(ord(dat[i-1]), i-1, val)
		self.addReading(ord(dat[i]), i, val)
		A = dat[i]

	self.addReading(ord(dat[samples-1]), samples-1, val)
	self.parsed_data = val
	self.samples = samples
    
    if getattr(self, 'parsed_data', None) is None: # case were no data has been loaded
	return

    val = self.parsed_data # restore local variables
    samples = self.samples
    
    # generate y axis ticks
    dataset = ()
    for i in range(self.LINES-1, -1, -1):
	dataset+=( ('bit %i' % i, val[i]),)
    
    # generate X axis range
    min_ = getattr(self, 'min_sample', 0)
    if min_ is None:
	min_ = 0
    max_ = getattr(self, 'max_sample', samples)
    if max_ is None or max_ > samples:
	max_ = samples
    
    x_range = ( min_ , max_ )

    # generate X axis ticks
    sample_step = (x_range[1]-x_range[0]) / 10
    xaxis = ()
    for i in range(0, 10):
	xaxis+=( (x_range[0] + i*sample_step, x_range[0] + i*sample_step), )
	
    yaxis = ()
    for i in range(0, self.LINES):
	yaxis += ( ('bit %s' % i, 0+i*2 ), )

    options = {
	    'legend': {
		'hide': True
		},
	    'shouldFill': False, 
	    'stroke': {
		'width': 1,
		'shadow': False,
		'hide': True},
		'background':{
		'hide': True,
		},
	    'axis':
	    {
		'tickSize': 2,
		'y': {
		    'hide': False,
		    'tickPrecision': 2,
		    'tickCount': self.LINES,
		    'range': (0, self.LINES*2+2),
		    'ticks': [dict(v=l[1], label=l[0]) for i, l in enumerate(yaxis)]
		},
		'x': {
		    'label': 'samples',
		    'tickPrecision': 0, # 0 decimals
		    'ticks': [dict(v=l[1], label=l[0]) for i, l in enumerate(xaxis)],
		    'range': x_range
		    },
	},
    }
    self.surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
    chart  = pycha.line.LineChart(self.surf, options)
    chart.addDataset(dataset)
    chart.render()

def draw(self, event, width, height):
    #print time.time(), 'draw'
    
    if getattr(self, 'window', None) is None:
	#print "no window on draw"
	return
	
    # Create the cairo context
    cr = self.window.cairo_create()

	# Restrict Cairo to the exposed area; avoid extra work
    cr.rectangle(event.area.x, event.area.y,
	event.area.width, event.area.height)
    cr.clip()

    self.updateInternalData(width, height)
	
    if self.surf is not None:
	#print 'set_source_surface'
	cr.set_source_surface(self.surf, 0, 0)
	cr.paint()
