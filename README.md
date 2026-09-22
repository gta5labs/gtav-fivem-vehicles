<div align="center">

# FiveLabs Vehicle DB

A simple, static GTA V / FiveM vehicle preview database for developers.

**Official FiveM vehicle data · Local preview images · GitHub Pages ready**

[Live Database](https://gta5labs.github.io/vehicle-db/) ·
[Vehicle JSON](https://gta5labs.github.io/vehicle-db/vehicles/index.json) ·
[Official FiveM Reference](https://docs.fivem.net/docs/game-references/vehicle-references/vehicle-models/)

</div>

---

## About

**FiveLabs Vehicle DB** is a lightweight browser for GTA V / FiveM vehicle models and preview images.

The project is intentionally simple: the website is a single `index.html`, while the generated vehicle database and preview images live inside the `vehicles/` folder.

The included setup script downloads vehicle information from the official FiveM vehicle reference and mirrors the official preview images locally, so developers can use predictable links hosted from this repository.

The interface follows the same simple viewer layout as the FiveLabs clothing database and includes:

- official FiveM vehicle categories in the sidebar
- an **All vehicles** view
- responsive vehicle preview grid
- adjustable preview size
- lazy-loaded images
- fullscreen preview lightbox
- click-to-copy direct image URLs
- dark and light appearance modes
- **dark mode by default**
- saved theme preference in the browser

---

## Quick setup

Clone or download the repository, then run:

```text
db_setup.bat
```

The setup script:

1. Downloads the official FiveM vehicle reference.
2. Reads the documented vehicle categories, display names, model names and hashes.
3. Downloads the official vehicle preview images.
4. Saves the previews into `vehicles/`.
5. Generates `vehicles/index.json`.
6. Generates `vehicles/index.js` for the static viewer.

No npm install, database server or web framework is required.

Python 3 is required to run the setup script.

---

## Data sources

Vehicle information:

```text
https://docs.fivem.net/docs/game-references/vehicle-references/vehicle-models/
```

Original preview images:

```text
https://docs-backend.fivem.net/vehicles/{model}.webp
```

The generated site serves its own local copies from the repository.

---

## Repository structure

```text
vehicle-db/
│
├── index.html
├── db_setup.bat
├── db_setup.py
├── README.md
├── .nojekyll
│
└── vehicles/
    ├── index.json
    ├── index.js
    ├── adder.webp
    ├── asbo.webp
    ├── zentorno.webp
    └── ...
```

`index.html` contains the entire viewer UI.

`vehicles/index.js` is used by the browser so the database also works when `index.html` is opened directly from disk.

`vehicles/index.json` is the developer-friendly JSON endpoint for hosted deployments.

---

## GitHub Pages

Run `db_setup.bat` **before committing** so the generated database and preview images exist in the repository.

Then enable GitHub Pages:

```text
Repository Settings
→ Pages
→ Deploy from a branch
→ main or master
→ /(root)
→ Save
```

For the `gta5labs/vehicle-db` repository the site URL is:

```text
https://gta5labs.github.io/vehicle-db/
```

---

## Direct vehicle image URLs

Every locally mirrored preview uses the vehicle model name as its filename:

```text
https://gta5labs.github.io/vehicle-db/vehicles/{model}.webp
```

Example:

```text
https://gta5labs.github.io/vehicle-db/vehicles/adder.webp
```

HTML:

```html
<img
  src="https://gta5labs.github.io/vehicle-db/vehicles/adder.webp"
  alt="Adder"
/>
```

JavaScript:

```js
const model = "adder";

const imageUrl =
  `https://gta5labs.github.io/vehicle-db/vehicles/${model}.webp`;
```

---

## JSON database

The complete generated database is available at:

```text
https://gta5labs.github.io/vehicle-db/vehicles/index.json
```

Example:

```js
const response = await fetch(
  "https://gta5labs.github.io/vehicle-db/vehicles/index.json"
);

const database = await response.json();

console.log(database.meta);
console.log(database.categories);
```

The JSON is grouped by the same vehicle categories shown in the sidebar.

A vehicle entry contains data such as:

```json
{
  "model": "adder",
  "displayName": "Adder",
  "hash": "3078201489",
  "signedHash": -1216765807,
  "hexHash": "0xB779A091",
  "path": "vehicles/adder.webp"
}
```

---

## Appearance

The viewer includes two appearance options in the bottom of the sidebar:

```text
Dark | Light
```

Dark mode is the default.

The selected appearance is saved in the browser with `localStorage`, so returning visitors keep their selected mode.

---

## Updating the database

To refresh the local database after the official FiveM vehicle reference changes, run:

```text
db_setup.bat
```

Existing valid preview images are reused, so the setup does not need to redownload everything every time.

To force a full image refresh, run the Python setup script with:

```text
python db_setup.py --overwrite
```

---

## Using the database in another FiveM project

You do not need to copy every image into another website.

For a vehicle model such as:

```text
zentorno
```

you can build the preview URL directly:

```js
function getVehiclePreview(model) {
  return `https://gta5labs.github.io/vehicle-db/vehicles/${model}.webp`;
}
```

That gives:

```text
https://gta5labs.github.io/vehicle-db/vehicles/zentorno.webp
```

This makes the repository useful for vehicle spawners, FiveM NUI menus, Discord bots, documentation websites and other developer tools.

---

## Credits

Vehicle reference data and original preview images are sourced from the official **Cfx.re / FiveM documentation**.

FiveLabs maintains this repository as a developer-friendly static mirror and browser.

This project is not an official Cfx.re, Rockstar Games or Take-Two Interactive product.

Grand Theft Auto V and related names, game assets and trademarks belong to their respective owners.

---

<div align="center">

**FiveLabs · Vehicle DB**

`https://gta5labs.github.io/vehicle-db/`

</div>
