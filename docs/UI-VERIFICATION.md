# Browser verification - 2026-09-04

Both live React interfaces were opened in the local browser, logged in with the seeded Alice account and visually inspected. The correct team edition and separate seeded collections were present. The Imposters interface created a real note titled "Local browser verification", saved it through the API, and archived it. Its team directory displayed the two member names and IDs supplied by the user. The note remains recoverable in Archive.

Both browser sessions were reloaded after migration from local Gunicorn to Docker, and remained authenticated with the original data. Outsiders retained three active notes; Imposters retained three active notes and the archived verification note. These are observations from this implementation session, not identity-stamped grading screenshots or claims of student work.

A narrow layout inspection exposed off-screen navigation to keyboard/accessibility users while closed. The mobile sidebar now becomes invisible until explicitly opened; whitespace in the mobile sign-in headline is preserved. Component tests also verify literal rendering of hostile content, API-backed saving and unsaved-draft protection.
