#! /bin/env python
# 
# Logic Analyzer based on avnet spartan3a-eval
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

 
import sys # if this one fails then we're REALLY SCREWED!

try:
    import pygtk
    pygtk.require("2.0")
    import gtk
    import gtk.glade
    import screen
    import gobject
    import cairo
    import serial
    import time
    from gtk import gdk
#    from port_chooser import PortChooser
    import os
    import pycha.line
    import random
    import threading
except Exception, err:
    print "missing library %s" % err
    sys.exit(1)

class LogicAnalyzer():
    
    def __init__(self):
	# init some variables
	path=os.path.join( os.path.dirname( os.path.realpath ( __file__ ) ), 'tools' ) # path to tools

	if hasattr(sys,"frozen") and sys.frozen in ["windows_exe", "console_exe"]:
	    path=os.path.join(os.path.dirname(sys.executable), 'tools')

	programmer = os.path.join(path, 'avs3a')
	port = '/dev/ttyACM0' # default port, gets overwritten by port chooser

	if sys.platform == 'win32':
    	    programmer = os.path.join(path, 'avprog', 'AvProg.exe')
	    port = 'COM1' # default port, gets overwritten by port chooser

        bit_file = os.path.join(path, 'analyzer.bit')

        self.glade=gtk.glade.XML('analyzer.glade')
        glade = self.glade

        glade.signal_connect("on_tool_open_clicked", self.on_tool_open_clicked)
        glade.signal_connect("on_menu_open_activate", self.on_tool_open_clicked)
        
        glade.signal_connect("on_tool_save_clicked", self.on_tool_save_clicked)
        glade.signal_connect("on_menu_save_activate", self.on_tool_save_clicked)
        
        glade.signal_connect("on_tool_record_clicked", self.on_tool_record_clicked)
        glade.signal_connect("on_tool_stop_clicked", self.on_tool_stop_clicked)
        glade.signal_connect("on_tool_select_port_clicked", self.on_tool_select_port_clicked)
        glade.signal_connect("on_tool_program_clicked", self.on_tool_program_clicked)
        glade.signal_connect("on_tool_limit_min_clicked", self.on_tool_limit_min_clicked)
        glade.signal_connect("on_tool_limit_max_clicked", self.on_tool_limit_max_clicked)
        
        glade.signal_connect("on_menu_exit_activate", gtk.main_quit)
        
        glade.signal_connect("on_menu_about_activate", self.on_menu_about)

        self.main = glade.get_widget("main")
        self.main.connect("delete-event", gtk.main_quit)
        self.__init__area()
        self.main.show()

	
    def __init__area(self):
        self.area = self.glade.get_widget("plot")
        area = self.area
        # now dynamically "modify" the drawingarea item
        area.data = ()
        area.surf = None
        area.port = None
        area.LINES = 8
        area.redraw_canvas = screen.redraw_canvas.__get__(area)
        area.expose = screen.expose.__get__(area)
        area.on_configure_event = screen.on_configure_event.__get__(area)
        area.addReading = screen.addReading.__get__(area)
        area.updateInternalData = screen.updateInternalData.__get__(area)
        area.draw = screen.draw.__get__(area)
        area.connect("expose_event", area.expose)
        area.getDat=screen.getDat.__get__(area)
        area.connect("configure_event", area.on_configure_event)
        
        self.status = self.glade.get_widget("statusbar")
        self.status.mycontextid = self.status.get_context_id("analyzer")
    
    def on_button_press(self, args):
        '''Base button handler dispatcher'''
        if args.name == 'tool_open':
            pass
            
    def on_menu_about(self, args):
	about = self.glade.get_widget("aboutdialog")
	about.run()
	about.destroy()
	    
    def on_tool_open_clicked(self, args):
        print "on_tool_open_clicked"
        chooser = gtk.FileChooserDialog(
            title="Open Log", 
            action=gtk.FILE_CHOOSER_ACTION_OPEN,
            buttons=(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_OPEN,gtk.RESPONSE_OK))
        chooser.set_default_response(gtk.RESPONSE_OK)
        filter = gtk.FileFilter()
        filter.set_name("Log Files")
        filter.add_pattern("*.analyzer")
        chooser.add_filter(filter)
        
        filter = gtk.FileFilter()
        filter.set_name("All Files")
        filter.add_pattern("*")
        chooser.add_filter(filter)
        response = chooser.run()
        
        if response != gtk.RESPONSE_OK:
            print "canceled"
            chooser.destroy()
            return
        
        filename = chooser.get_filename()
        chooser.destroy()
        self.area.data = ()
        self.area.port = open(filename)


    def on_tool_save_clicked(self, args):
        print "on_tool_save_clicked"
        chooser = gtk.FileChooserDialog(
            title="Save Log", 
            action=gtk.FILE_CHOOSER_ACTION_SAVE,
            buttons=(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_OPEN,gtk.RESPONSE_OK))
        chooser.set_default_response(gtk.RESPONSE_OK)
        
        filter = gtk.FileFilter()
        filter.set_name("Log Files")
        filter.add_pattern("*.analyzer")
        chooser.add_filter(filter)
        
        filter = gtk.FileFilter()
        filter.set_name("All Files")
        filter.add_pattern("*")
        chooser.add_filter(filter)

        response = chooser.run()
        
        if response != gtk.RESPONSE_OK:
            print "canceled"
            chooser.destroy()
            return
        
        filename = chooser.get_filename()
        chooser.destroy()
        
        out = file(filename, "w")
        out.write(self.area.data)
        out.close()

    def on_tool_record_clicked(self, args):
        self.area.port = serial.Serial(self.port, timeout=0,
            baudrate=115200*2, bytesize=8, parity='N',
            stopbits=2)
        self.area.port.flushInput()
        self.area.data = ""
        self.start_time = time.time()
        gobject.timeout_add(1000, self.update_status)
        gobject.timeout_add(200, self.area.redraw_canvas)

    def on_tool_stop_clicked(self, args):
        if type(self.area.port) == serial.Serial:
            self.area.port.close()
            self.area.port = self.area.data

    def on_tool_select_port_clicked(self, args):
        dialog = gtk.Dialog('Select Port', self.main,
            gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
            (
                gtk.STOCK_OK, gtk.RESPONSE_ACCEPT,
                    gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT
                )
                )
        
        valid_ports = ""    	
        if sys.platform == 'linux2':
	        valid_ports = [ '/dev/%s' % b for b in os.listdir('/dev/') if b.startswith('ttyACM') ]
        elif sys.platform == 'win32':
	        valid_ports = [ 'COM%s' % b for b in range(1,20) ]
        else:
	        self.status.push(self.status.mycontextid, "Not supported platform" )
	        return

        model = gtk.TreeStore(str)
        
        for port in valid_ports:
            model.append(None, [port])
        list_view = gtk.TreeView(model)
        
        column = gtk.TreeViewColumn('Port Name')
        cell = gtk.CellRendererText()
        column.pack_start(cell, True)
        column.add_attribute(cell, 'text', 0)
        list_view.append_column(column)
        
        selection = list_view.get_selection()
        selection.set_mode(gtk.SELECTION_SINGLE)
        
        dialog.vbox.add(list_view)
        dialog.show_all()
        
        response = dialog.run()
        value = None
        
        if response != gtk.RESPONSE_ACCEPT:
            dialog.destroy()
            return
        
        model, iter = selection.get_selected()
        port = model.get(iter, 0)[0]
        self.port = port
        dialog.destroy()
        print self.port

    def on_tool_program_clicked(self, args):
        print sys.platform
        if sys.platform not in [ 'linux2', 'win32' ]:
            self.status.push(self.status.mycontextid, "Not supported platform" )
            return

        self.status.push(self.status.mycontextid, "Programming board..." )
        os.system('%s -b %s -p %s -s -v' % (self.programmer, self.bit_file, self.port) )        
        self.status.push(self.status.mycontextid, "Board is ready now" )
	
    def display_input_dialog(self, title, text, default_value, parent=None):
        if parent is None:
            parent = self.main
        dialog = gtk.Dialog(title, parent,
            gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
            (
                gtk.STOCK_OK, gtk.RESPONSE_ACCEPT,
                    gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT
                )
                )
#    	window = dialog.get_action_area()
        dialog.vbox.add(gtk.Label("%s:" % text))
        input = gtk.Entry()
        input.set_text(default_value)
        dialog.vbox.add(input)
        dialog.show_all()
        
        response = dialog.run()
        value = None
        if response == gtk.RESPONSE_ACCEPT:
            value = input.get_text()
        dialog.destroy()
        return (response==gtk.RESPONSE_ACCEPT, value)

    def on_tool_limit_min_clicked(self, args):
        response, reply = self.display_input_dialog(
            "Input Lower Sample to see",
                "Lowest Sample",
                str(getattr(self.area, 'min_sample', ''))
                )
                
        if not response:
            return
        
        if reply is not None and len(reply) > 0:
            try:
                self.area.min_sample = max(int(reply),0)
            except:
                gtk.MessageDialog(type=gtk.MESSAGE_ERROR, message_format="Not valid format")
        else:
            self.area.min_sample = None
        self.area.redraw_canvas()

    def on_tool_limit_max_clicked(self, args):
        response, reply = self.display_input_dialog(
            "Input Maximum Sample to see",
                "Maximum Sample",
                str(getattr(self.area, 'max_sample', ''))
                )
                
        if not response:
            return
        
        if reply is not None and len(reply) > 0:
            try:
            	self.area.max_sample = int(reply)
            except:
            	gtk.MessageDialog(type=gtk.MESSAGE_ERROR, message_format="Not valid format")
        else:
            self.area.max_sample = None
        self.area.redraw_canvas()

    def update_status(self):
        if type(self.area.port) is serial.Serial:
            elapsed = int(time.time() - self.start_time)

        try:
            self.status.pop(self.area.mycontextid) # clear status bar
        except:
            pass
            
        self.status.push(self.status.mycontextid, "%s %s %s" % ("Recorded for", elapsed, "seconds"))
        print "update status"
        return type(self.area.port) is serial.Serial

if __name__=='__main__':
    analyzer = LogicAnalyzer()
    gtk.main()
