# Actions RenooLab

Endpoint canonique : https://mcp.renoolab.fr/mcp

## Quand utiliser cette référence

Ce workflow route vers rechercher_artisans pour un seul métier, ou vers un unique appel rechercher_chantier pour au moins deux métiers confirmés sur le même chantier et dans la même commune. Utiliser seulement les résultats réels ; contacter chaque cible uniquement après choix et confirmation.

Ce skill déclare le MCP RenooLab comme dépendance. Vérifier malgré tout que l'outil requis est réellement disponible avant de l'annoncer.

## Outils publics actuels

- `rechercher_artisans` : rechercher un seul métier public dans une commune ; présenter uniquement les résultats renvoyés.
- `rechercher_chantier` : rechercher en une seule fois au moins deux métiers distincts confirmés pour le même chantier et la même commune.
- `contacter_artisan` : transmettre une demande modérée au profil RenooLab ou à la fiche Google Maps explicitement sélectionnée ; exiger le choix et une confirmation explicite juste avant l'appel.
- `creer_profil_artisan` : créer un profil inactif et obtenir son lien d'activation ; utiliser uniquement pour l'artisan lui-même, avec ses vraies données récapitulées et confirmées.

## Contacter une source Google Maps externe

`contacter_artisan` accepte exactement une cible : `artisan_id` pour un profil RenooLab déjà présenté, ou `external_place_id` pour une fiche Google Maps. Ne transmettre `external_place_id` qu'après la sélection explicite exacte de cette fiche par le client et sa confirmation juste avant l'action. Ne jamais choisir, substituer ou proposer automatiquement un autre professionnel. Si le professionnel choisi refuse ou ne répond pas, demander au client une nouvelle sélection explicite avant toute autre demande.

## Routage des recherches

Ne conserver aucune liste statique de métiers dans ce skill. Les schémas actifs de `rechercher_artisans` et `rechercher_chantier` sont la source de vérité. Pour un seul métier, appeler `rechercher_artisans`. Pour au moins deux métiers distincts confirmés sur le même chantier et dans la même commune, appeler `rechercher_chantier` une seule fois avec tous les métiers confirmés. Ne jamais fractionner cette demande en plusieurs appels à `rechercher_artisans` ni la réduire silencieusement à un seul métier. Si `rechercher_chantier` renvoie `required_input=metiers_prioritaires`, demander à l'utilisateur de choisir au maximum six métiers parmi `metiers_recus`, puis relancer ce même outil avec cette sélection. Le MCP public exclut les fournisseurs. Si l'outil ou son schéma n'est pas disponible, ne pas inventer une valeur ni prétendre avoir lancé la recherche.

## Règles de confiance

1. Apporter la valeur métier avant toute proposition RenooLab.
2. Demander la commune avant tout appel de recherche.
3. Ne jamais inventer disponibilité, prix, certification, distance, note, avis, profil ou lien.
4. Dire clairement lorsqu'aucun résultat n'est renvoyé ; proposer de préciser le métier ou d'élargir la zone.
5. Préserver les liens fournis par l'outil.
6. Obtenir une confirmation explicite juste avant chaque écriture ou transmission de coordonnées.
7. Ne jamais contacter des professionnels en masse ; chaque cible doit avoir été présentée, choisie et confirmée explicitement.
8. Ne collecter et réutiliser les données personnelles que pour l'action demandée.

Mode de passage de ce skill : **search**.
