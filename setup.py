from distutils.core import setup
import setup_translate

pkg = 'Extensions.CzechMeteo'
setup (name = 'enigma2-plugin-extensions-czechmeteo',
	version = '2.0.3',
	description = 'czech meteo information viewer',
	packages = [pkg],
	package_dir = {pkg: 'plugin'},
	package_data = {pkg: ['*.png', '*.xml', '*/*.png', 'locale/*.pot', 'locale/*/LC_MESSAGES/*.mo']},
	cmdclass=setup_translate.cmdclass, # for translation
	)
