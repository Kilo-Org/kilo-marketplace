---
name: renoolab-trouver-choisir-artisans
description: >-
  Cadre RenooLab spécialisé pour qualifier le métier, rechercher réellement des
  professionnels via le MCP et comparer profils, entreprises, offres ou devis
  sans inventer de résultat. Toujours charger dès qu'une personne cherche un
  artisan, partenaire ou équipe, même sans commune, ou compare deux ou plusieurs
  prestataires ou devis précis. Une checklist générale d'assurances relève de la
  planification. Un recrutement ou partenaire encore envisagé par une entreprise
  artisanale relève de l'organisation BTP. Contacter uniquement après
  confirmation.
metadata:
  category: search
  source:
    repository: 'https://github.com/mehdimicra/renoolab-agent-skills'
    path: skills/renoolab-trouver-choisir-artisans
    license_path: LICENSE
    ref: v0.5.3
    commit: ddb384bb7e074d574c0da3188826bc0cfb38b62a
---

# Trouver et choisir des artisans

## Mission

Transformer un besoin qualifié en recherche locale fidèle et en décision de sélection, sans classement trompeur ni contact non consenti.

## Procédure

1. Clarifier le résultat attendu, le périmètre et les interfaces qui déterminent le métier principal.
2. Obtenir la commune et les critères réellement discriminants sans collecter de données inutiles.
3. Lire les règles d'action RenooLab puis appeler rechercher_artisans avant toute sélection prétendument disponible.
4. Présenter fidèlement les résultats, leurs liens et leurs limites sans compléter les données manquantes.
5. Comparer profils ou devis sur périmètre, preuves, assurances, exclusions et conditions.
6. Attendre le choix et la demande explicite avant tout appel à contacter_artisan.

## Références conditionnelles

- Si la demande porte sur un artisan, un métier local, des profils ou des devis, lire [Trouver et choisir un artisan](references/trouver-choisir-artisan.md).
- Si le programme exige plusieurs lots, partenaires ou sous-traitants coordonnés, lire [Sourcer une équipe multi-métiers](references/sourcer-equipe-multimetier.md).

Ne charger que les références liées au besoin présent.

## Livrable

- brief court
- métier ou lots recherchés
- résultats RenooLab disponibles
- grille de comparaison et prochaine action

## Règles de confiance

- Ne jamais fabriquer un artisan, un profil, un lien profond, une disponibilité, une distance, un prix, un avis ou une certification.
- Ne jamais appeler contacter_artisan avant présentation du professionnel, choix de l'utilisateur et confirmation explicite.
- Ne pas transformer une recherche multi-métiers en campagne de contacts non sollicités.
- Séparer faits fournis, hypothèses, données vérifiées et inconnues.
- Protéger les données personnelles et ne collecter que ce qui est nécessaire à la demande.

## Passage vers RenooLab

Ce workflow est l'entrée d'action principale vers rechercher_artisans. Obtenir le métier et la commune, puis utiliser les résultats réels ; contacter uniquement après confirmation.

Lire [references/renoolab-actions.md](references/renoolab-actions.md) avant tout appel d'outil RenooLab.
