.. _developer_label:

Für EntwicklerInnen
===================

Der Quellcode ist auf `GitHub <https://github.com/rl-institut/WAM_APP_stemp_mv>`_ verfügbar.
Details zur Installation finden sich unter :ref:`install_label`.

Technologien
------------

Django-Kosmos
-------------

Diese StEmp-Web-Applikation ist Teil des WAM-Applikationen-Kosmos_ des
Reiner Lemoine Instituts (RLI). Die Bezeichnung WAM steht hierbei für
*Web Applications and Maps* und stellt eine Kategorie von Applikationen dar,
welche am RLI erstellt werden. Dies sind hauptsächlich Web-Applikationen,
die mit Hilfe von Karten arbeiten und oder bei denen im Hintergrund Berechnungen
stattfinden, dessen Ergebnis an die NutzerInnen visuell zurückgegeben wird.
Einige der WAM-Applikationen sind mit dem RLI-eigenen Web-Applikationen-Framework
mit dem Namen WAM_ erstellt worden, andere WAM-Applikationen basieren auf anderen
Frameworks oder sind freie Implementationen ohne Framework-Basis.

Diese StEmp-Web-Applikation des RLI nutzt das Git-Projekt WAM_ als Basis-Projekt.
Das verwendete WAM-Basis-Projekt baut auf dem Django_-Web-Framework auf,
welches Python als Programmiersprache verwendet. Django hat eine gewisse
Lernkurve, deswegen kann es Sinn machen, sich bei Bedarf zuerst mit dem
zugrunde liegenden Web-Framework Django zu beschäftigen, bevor mit der Arbeit
an einer auf Django basierenden WAM-Applikation begonnen wird. Für das Erlernen
des Umgangs mit Django gibt es sehr viel Lernmaterial Dritter, weswegen im
Folgenden in dieser Dokumentation auf einige dieser Anleitungen und
Dokumentationen zum Erlernen von Django verwiesen werden soll. Anschließend
wird im nächsten Abschnitt auf der auf Django basierenden WAM-Projektbasis
eingegangen.

Tutorials und Informationen zu Django:

- Das Django `getting started Tutorial`_
- Tutorial_ einer einfachen Geo-Applikation in Django
- Die offizielle Django-Dokumentation_
- Die Django-Design-Philosophie_

WAM-Kosmos
----------

Wie im vorherigen Abschnitt *Django-Kosmos* bereits kurz angesprochen, verwendet
dieses Projekt das RLI eigene Web-Applikationen-Framework WAM_.
Das WAM-Framework nutzt hierfür Django also Unterbau. Der Django-Unterbau ist
dahingehend umgearbeitet, dass er besonders gut auf die Bedürfnisse für die
Entwicklung von Applikationen am RLI zugeschnitten ist und er sich von Projekt
zu Projekt als Projektbasis wiederverwenden lässt. Im Folgenden soll deshalb
kurz auf das WAM-Framework eingegangen werden.

Das WAM-Framework setzt mehrere zugrundlegende Prinzipien konsequent um:

- die initiale Konfigurationsarbeit für auf der WAM basierende Web-Applikationen
  soll minimiert und wenn möglich automatisiert werden.
- das Zusammenfassen von häufig benötigten Funktionalitäten und die Integration
  dieser Funktionalitäten in die WAM-Projektbasis, für die einfache Verwendung
  von auf der WAM basierenden Web-Applikationen.
- eine gemeinsame Projektbasis in der multiple Applikationen angedockt sind
  minimieren den Wartungsaufwand des Gesamtsystems zur Laufzeit.

Der Grund für die Umsetzung dieser Prinzipien ist die Minimierung von Aufwänden
bei der Erstellung und dem Betrieb von Web-Applikationen, welche am RLI und
Allgemein im Bereich der Erneuerbaren-Energien-Forschung und -Entwicklung
benötigt werden. Durch diese Herangehensweise profitieren bereits die beiden
(stemp_abw_, stemp_mv_) im Rahmen des ENavi-Projektes vom RLI entwickelten
StEmp-Tools, welche beide das WAM_-Framework als Unterbau nutzen.

Für die Sichtbarmachung von Aufbau und Nutzung des WAM-Frameworks gibt es eine
eigenständige WAM-Dokumentation_, welche weiterführende Informationen enthält.


.. _Django: https://www.djangoproject.com/
.. _Django-Design-Philosophie: https://docs.djangoproject.com/en/2.2/misc/design-philosophies/
.. _Django-Dokumentation: https://docs.djangoproject.com/en/2.2/
.. _getting started Tutorial: https://www.djangoproject.com/start/
.. _stemp_abw: https://github.com/rl-institut/WAM_APP_stemp_abw
.. _stemp_mv: https://github.com/rl-institut/WAM_APP_stemp_mv
.. _Tutorial: https://realpython.com/location-based-app-with-geodjango-tutorial/
.. _WAM: https://github.com/rl-institut/WAM
.. _WAM-Applikationen-Kosmos: https://wam.rl-institut.de/
.. _WAM-Dokumentation: https://wam.readthedocs.io/en/latest/
