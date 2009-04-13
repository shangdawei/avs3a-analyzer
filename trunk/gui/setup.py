from distutils.core import setup
import py2exe

setup(
	name='analyzer',
	description='Logic Analyzer',
	version='1.0',
	#windows=['analyzer.py'],
	console=['analyzer.py'],
	authors= 'Naranjo Manuel Francisco, Martin Rassia',
    	options = {
                  'py2exe': {
                      'packages':'encodings',
                      'includes': 'cairo, pango, pangocairo, atk, gobject',
                  }
              },

    	data_files=[
                   'analyzer.glade',
      ]
)
