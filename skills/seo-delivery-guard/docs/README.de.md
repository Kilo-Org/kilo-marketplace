# SEO Delivery Guard

**An den offiziellen Grenzen von Google Search ausgerichtete SEO-Entwicklungs- und Release-Governance für KI-Programmieragenten.**

[![Codex Skill](https://img.shields.io/badge/Codex-Skill-111827?logo=openai&logoColor=white)](../SKILL.md)
[![Version 0.1.0](https://img.shields.io/badge/version-0.1.0-2563eb)](../CHANGELOG.md)
[![MIT License](https://img.shields.io/badge/license-MIT-16a34a)](../LICENSE)
[![Documentation languages: 10](https://img.shields.io/badge/docs-10%20languages-7c3aed)](../README.md#documentation)
[![GitHub source](https://img.shields.io/badge/GitHub-pangxin12345%2Fseo--delivery--guard-181717?logo=github&logoColor=white)](https://github.com/pangxin12345/seo-delivery-guard)
[![Official website](https://img.shields.io/badge/website-once--email.com-0f766e?logo=googlechrome&logoColor=white)](https://once-email.com)
[![skills.sh](https://skills.sh/b/pangxin12345/seo-delivery-guard)](https://skills.sh/pangxin12345/seo-delivery-guard)

[English](../README.md) · [简体中文](README.zh-CN.md) · [Español](README.es.md) · [Português do Brasil](README.pt-BR.md) · [Deutsch](README.de.md) · [Français](README.fr.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Bahasa Indonesia](README.id.md) · [Tiếng Việt](README.vi.md)

SEO-Audits finden Probleme. **SEO Delivery Guard hilft einem KI-Programmieragenten, akzeptierte Befunde bis zur Implementierung, Prüfung, Veröffentlichung und Produktionsverifikation zu begleiten.**

Der Skill ersetzt keine Crawler, Performance-Werkzeuge, Inhaltsanalysen, Validatoren für strukturierte Daten, SERP-Recherchen oder Search-Console-Daten. Er koordiniert vorhandene Fähigkeiten, wendet Projektregeln an und trennt Release-Blocker von optionalen Empfehlungen.

## Warum dieser Skill existiert

- Ein Canonical kann im Quellcode stimmen und im erzeugten Ergebnis falsch sein.
- Eine ungeprüfte Übersetzung kann zu früh in die Sitemap gelangen.
- Strukturierte Daten können nicht sichtbare Tatsachen behaupten.
- Eine Robots-Anweisung kann fälschlich als Zugriffsschutz behandelt werden.
- Ein Gesamtwert kann einen Indexierungs- oder Datenschutzblocker verdecken.
- Ein Kandidat kann bestehen, während die Produktion andere Metadaten liefert.
- Ein Release kann vor dem erneuten Crawling voreilig als erfolgreich gelten.

## Kernfunktionen

- Wählt für jede Änderung die kleinste sinnvolle SEO-Analysekombination.
- Liest Projektregeln zu Entwicklung, Datenschutz, Lokalisierung, Analytics, Werbung, Tests und Veröffentlichung.
- Löst widersprüchliche Empfehlungen anhand einer klaren Rangfolge.
- Erfasst Quelle, Zeitpunkt, Sicherheit, Schweregrad, Maßnahme, Prüfebene und Rollback-Folge.
- Hält harte Blocker binär und außerhalb gemittelter Gesundheitswerte.
- Vergleicht den suchrelevanten Vertrag vor und nach einer Änderung.
- Trennt Quellcode, erzeugtes Artefakt, Browser, öffentliches HTTP, Labordaten, Erstanbieterdaten und Fremdschätzungen.
- Behandelt Indexierung, Ranking, Traffic, Rich Results, Werbeprüfung und KI-Sichtbarkeit bis zur Verifikation als ausstehend.
- Verlangt eine Entscheidung zwischen Beibehalten, Verbessern, Zusammenführen, `noindex` oder Entfernen; 301 gilt nur für ein wirklich gleichwertiges Ziel, sonst bleiben ehrliche `404/410`-Antworten erhalten.

## Was er nicht tut

- Kein weiterer Website-Crawler und kein All-in-one-SEO-Audit.
- Keine Bindung an einen bestimmten Anbieter, eine API, MCP oder einen Begleit-Skill.
- Keine URL-Einreichung, Kontenänderung, Veröffentlichung oder Bereitstellung ohne Aufgabenfreigabe.
- Keine Garantie für Indexierung, Ranking, Traffic, Rich Results, Werbefreigabe oder KI-Zitate.

## Eingaben, Ausgaben und Grenzen

Stelle nur die notwendige öffentliche URL, den Repository-Pfad, die beabsichtigte Änderung, Zielgruppe, Indexierungsabsicht, Sprachen und bereinigte Nachweise bereit. Keine Passwörter, Cookies, privaten Schlüssel, vollständigen Analytics-Exporte oder sensiblen Daten. Die Ausgabe trennt Regeln, Blocker, Hinweise, Unbekanntes, Beweisgrenzen, Maßnahmen, Prüfebenen, Produktionsstatus und ausstehende externe Ergebnisse.

Der Skill lehnt Rankingmanipulation, erfundene Erfahrung oder Belege, Doorway-Seiten, wertlose Masseninhalte, Umgehung von Zugriffskontrollen, Datenoffenlegung und falsche Zertifizierungen ab. Eine nicht erreichbare Seite oder Analyse bleibt unbekannt und gilt nicht als bestanden.

Jede indexierbare Seite muss eine Aufgabe lösen, die die stärkste bestehende URL nicht erfüllt. Maschinelle Übersetzung und Strukturprüfungen beweisen keine Sprachqualität; jede öffentliche Sprachfassung braucht fachliche und sprachliche Prüfung.

## Installation

Installiere den Skill über einen unterstützten Marktplatz oder kopiere den vollständigen Ordner `seo-delivery-guard` in das Skill-Verzeichnis deines KI-Agenten. Skills neu laden oder eine neue Sitzung starten und aufrufen:

```text
$seo-delivery-guard
```

Das öffentliche Paket enthält nur Textanweisungen und Metadaten – keine ausführbaren Dateien, Crawler, API-Schlüssel oder betriebssystemspezifischen Komponenten.

## Grenzen von Google Search

Aussagen über Google Search müssen auf aktueller offizieller Dokumentation oder verifizierten Erstanbieterdaten beruhen. Drittwerkzeuge liefern Hinweise, definieren aber weder Indexierungsentscheidungen noch Rankingfaktoren, Rich Results oder KI-Funktionen von Google.

SEO Delivery Guard ist ein unabhängiges Open-Source-Projekt und weder mit Google verbunden noch von Google zertifiziert, gesponsert oder empfohlen.

## Herausgeber

- Herausgeber und offizielle Website: [once-email.com](https://once-email.com)
- Entwicklerin: helen.jar
- GitHub: [pangxin12345](https://github.com/pangxin12345)
- Öffentlicher Support: [tiantuowl@gmail.com](mailto:tiantuowl@gmail.com)

MIT-Lizenz · Version 0.1.0

Änderungen stehen in [CHANGELOG.md](../CHANGELOG.md).
