.. _install_label:

Installation
============

Das Tool kann bei Bedarf auch lokal eingerichtet werden.
Zur Vereinfachung kann das Tool mittels Docker_ eingerichtet werden.

Voraussetzungen
---------------

* git ist installiert.
* Docker_ und Docker-Compose_ sind installiert.

.. _Docker: https://docs.docker.com/install/
.. _Docker-Compose: https://docs.docker.com/compose/install/

Installation
------------

Zunächst muss ein WAM-Server mittels Docker aufgesetzt werden.
Anschließend kann das StEmp-MV Tool integriert werden.

Installation der WAM
####################

Für die Installation wird folgende Ordnerstruktur eingerichtet:

.. code-block:: bash

  wam_docker (Name beliebig)
  +-- docker (Enthält Docker Konfiguration und WAM-Codebasis)
  |   +-- docker-compose.yml
  |   +-- WAM (WAM-Codebasis; hier können später weitere Apps integriert werden)
  +-- config (Konfiguration für WAM und integrierte Apps)
  |   +-- config.cfg

.. note::
  Änderungen an dieser Struktur müssen in der Konfigurationsdatei bzw. in der Docker-Konfiguration (docker-compose.yml) berücksichtigt werden.

Die Einrichtung der Ordnerstruktur geschieht folgendermaßen:

.. code-block:: bash

  mkdir wam_docker
  cd wam_docker
  mkdir docker
  mkdir config
  cd docker
  git clone https://github.com/rl-institut/WAM.git
  cp WAM/docker-compose.yml .
  cp WAM/.config/config.cfg ../config/

Anschließend müssen die beiden Konfigurationsdateien (`docker-compose.yml` und `config.cfg`) angepasst werden.
Abschließend werden mit folgendem Befehl (aus dem `docker`-Ordner  heraus) die Images erstellt und die Container gestartet:

.. code-block:: bash

  sudo docker-compose up -d --build

Der WAM-Server sollte nun unter 127.0.0.1:5000 erreichbar sein.

Einbindung der StEmp-MV App
###########################

Die StEmp-MV App kann nun folgendermaßen in die WAM-Struktur eingebunden werden (ausgehend vom Ordner `wam_docker`):

.. code-block:: bash

  cd docker/WAM
  git clone https://github.com/rl-institut/WAM_APP_stemp_mv.git stemp

.. note::
  Die StEmp-MV App muss im Ordner `stemp` installiert sein, da sonst die internen Verweise nicht funktionieren.
  Sollte das Repository ohne Namenszusatz geklont worden sein, kann das Repository einfach umbenannt werden.

Die neue App `stemp` kann nun für die WAM aktiviert werden, in dem sie in der `docker-compose.yml` Datei unter `celery->build->args->WAM_APPS` hinzugefügt wird:

.. code-block:: bash

  celery:
    restart: unless-stopped
    build:
      context: ./WAM
      args:
        - WAM_APPS=stemp
    ...

Folgender Konfigurationsblock muss der Konfigurationsdatei (`config/config.cfg`) zusätzlich hinzugefügt werden:

.. code-block:: bash

  [STEMP]
    ACTIVATED_SCENARIOS=gas,bhkw,bio_bhkw,oil,woodchip,pv_heatpump
    DB_RESULTS=LOCAL
    DB_SCENARIOS=LOCAL

Dort können u.a. folgende Konfigurationen vorgenommen werden:

ACTIVATED_SCENARIOS
  die zur Verfügung stehenden Technologien
DB_RESULTS
  Name der Datenbank (muss unter `WAM->Databases` konfiguriert sein), in der die Ergebnisse gespeichert werden sollen
DB_SCENARIOS
  Name der Datenbank, in der die verwendeten Parameter liegen

Das WAM-Image muss nun neu kompiliert werden.
Dabei wird die StEmp-MV App in das Image kopiert und alle zusätzlichen Abhängigkeiten der neuen App installiert:

.. code-block:: bash

  cd docker
  sudo docker-compose up -d --build

Der Server (mit integrierter StEmp-MV App) sollte jetzt wieder unter 127.0.0.1:5000 erreichbar sein.

Abschließend müssen alle benötigten Parameter, Zeitreihen und andere Daten *einmalig* in die Datenbank migriert werden.
Dies geschieht über ein Skript das innerhalb des Docker Containers (der Container muss dafür in Betrieb sein) gestartet werden muss:

.. code-block:: bash

  # Startet eine bash innerhalb des Containers:
  sudo docker exec -it wam bash
  # Fügt die WAM dem PYTHONPATH hinzu; notwendig damit das queries.py Skript die WAM module nutzen kann
  export PYTHONPATH=$PYTHONPATH:/code
  python stemp/db_population/queries.py all
