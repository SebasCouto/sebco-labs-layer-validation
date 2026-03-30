# TECH READ QA TEAM

Esta guía se enfoca en asegurar la compatibilidad con los sistemas operativos [macOS](https://es.wikipedia.org/wiki/MacOS)<img src="https://raw.githubusercontent.com/FortAwesome/Font-Awesome/master/svgs/brands/apple.svg" alt="MacOS" width="15" height="25"> & [Windows](https://es.wikipedia.org/wiki/Microsoft_Windows)<img src="https://raw.githubusercontent.com/FortAwesome/Font-Awesome/master/svgs/brands/windows.svg" alt="Windows" width="15" height="25"> al configurar un proyecto [Python](https://www.python.org/)<img src="https://raw.githubusercontent.com/FortAwesome/Font-Awesome/master/svgs/brands/python.svg" alt="Python" width="15" height="25"> con Visual Studio Code, utilizando Pytest para la ejecución de pruebas.

Es imperativo que Python esté instalado y configurado correctamente en el sistema operativo de elección antes de seguir con la configuración del proyecto.
* __Windows__: En el caso de Windows, es recomendable seleccionar la opción 'Add Python to PATH' durante la instalación para integrar Python en el PATH del sistema, lo que facilitará el acceso y la gestión de módulos y paquetes en nuestros proyectos.
   *  <span style="color: #ff0000; font-size: 18px;">&#9888;</span> Paso Previo: Validación de Versiones de winget y git:
      - Antes de comenzar con la ejecución de los tests, es necesario asegurarse de que las versiones de winget y git estén actualizadas en tu sistema. Para facilitar este proceso, hemos incluido un archivo .bat ```actualizar_winget_y_git.bat``` que se puede ejecutar desde la terminal de tu sistema operativo. También este archivo se encuentra en la ruta documentacion de este repositorio y se encarga de verificar y actualizar automáticamente ambas herramientas en un solo paso.

* __macOS__: Para agregar el directorio de la raíz del proyecto a la variable de entorno PYTHONPATH debemos:
   - Abrir la terminal de Visual Studio Code y ejecuta el siguiente comando para agregar el directorio raíz del proyecto a la variable de entorno PYTHONPATH: 
      - (__Zsh__) ```export PYTHONPATH=..ruta local de tu proyecto/tech-red-qa"```.
      - (__Bash__) ```export PYTHONPATH=:..ruta local de tu proyecto/tech-red-qa```.
      - (__Command Prompt__) ```set PYTHONPATH=..ruta local de tu proyecto\tech-red-qa```
      - (__Power Shell__) ```$env:PYTHONPATH = "..ruta local de tu proyecto\tech-red-qa"```

   * <span style="color: #ff0000; font-size: 18px;">&#9888;</span> Ten en cuenta que la configuración de `PYTHONPATH` que estableces con el comando export `PYTHONPATH=...` en la terminal de Visual Studio Code es efectiva solo para la sesión actual de la terminal. Esto significa que la configuración se perderá una vez que cierres la terminal o reinicies tu sistema. Si deseas hacer que la configuración sea persistente y se aplique cada vez que abres una nueva terminal o reinicias tu sistema, puedes agregar el comando a un archivo de inicio de shell.


# GUIA STEP-BY-STEP
- &rarr;[Main Setup](https://github.com/SebasCouto/tech-red-qa/blob/main/doc/1.%20Main%20setup.md)
- agregar lo de la activacion de (venv)
```Administrator@USER MINGW64 /e/repositorios/Personal/tech-red-qa (reports) $ source .venv/Scripts/activate```
y luego hacer
```pip install -r requirements.txt```

- setear la ariable de entorno ```PYTHONPATH``` con el path raíz del proyecto desde donde se ejecuta pytest.
- &rarr;[Configurar GitBash en Visual Studio Code 1.40+](https://github.com/SebasCouto/tech-red-qa/blob/main/doc/2.%20Configurar-git-bash-vscode.md)
- &rarr;[Configurar un flujo CI/CD con GitHub Actions para tu proyecto](https://github.com/SebasCouto/tech-red-qa/blob/main/doc/3.%20Github_Action.mdd)
- &rarr;[Configurar un reporte HTML local y remoto](https://github.com/SebasCouto/tech-red-qa/blob/main/doc/4.%20SetupArtifactHTMLReport.md)
