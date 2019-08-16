.. _install_label:

Installation
============

Das Tool kann bei Bedarf auch lokal eingerichtet werden.
Zur Vereinfachung kann das Tool mittels `Docker <https://www.docker.com/>`_ eingerichtet werden.

Voraussetzungen
---------------

* git ist installiert.
* `Docker <https://docs.docker.com/install/>`_ und `Docker-Compose <https://docs.docker.com/compose/install/>`_ sind installiert.

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

.. code-block:: bash
  [STEMP]
    ACTIVATED_SCENARIOS=gas,bhkw,bio_bhkw,oil,woodchip,pv_heatpump
    ACTIVATED_VISUALIZATIONS=lcoe,ranked_invest,ranked_co2
    DB_RESULTS=LOCAL
    DB_SCENARIOS=LOCAL