# VinylTracklist 1.0

Programa per a Windows (de 7 a 11) per preparar el **tracklist de les cares d'un vinil** a partir dels WAV.

## Què fa

- Dues zones, **Cara A** i **Cara B**: s'hi carreguen els WAV amb «Afegir WAV…» o arrossegant-los (o una carpeta) des de l'Explorador.
- **Cada cop que s'afegeixen WAV, la cara es reordena sencera alfabèticament** pel nom del fitxer (ordre natural: A2 abans que A10; sense tenir en compte accents). Després es pot canviar l'ordre arrossegant els temes (també d'una cara a l'altra), amb ▲ ▼ / «→ Cara B», o amb el botó dret.
- El **títol** surt del nom del fitxer: sense extensió, `_` → espai i sense la numeració inicial (`A04_TE_BUSCO.wav` → «TE BUSCO»). Doble clic per canviar-lo.
- Sota cada tema: **kHz, bits, enter (PCM) o coma flotant, mono/estèreo**.
- **Pauses entre temes**: casella per activar-les, 2,0 s per defecte, valor global editable i **pausa pròpia** per a cada separació («restablir» la torna al valor global).
- Total de cada cara (música + pauses) amb **barra verda / groga / vermella** segons el temps recomanat, i panell de **temps recomanats per cara** (editables a *Eines › Configuració*).
- **Avisos**: WAV en coma flotant, fitxers il·legibles o incomplets, formats comprimits, freqüències o resolucions barrejades, mono, cara massa llarga, fitxers repetits.
- **Dos informes**, en TXT, Word (.docx) i PDF:
  - **Informe propi** (castellà): tracklist complet amb temps recomanat i avisos.
  - **Informe per a fàbrica** (anglès): artista, títol, referència, format; per cara posició, títol, durada, pausa, format d'àudio i total de la cara. Sense temps recomanat ni avisos.
- Pestanya **Informe**: vista prèvia a pantalla de l'informe triat, amb el mateix disseny que el PDF.
- **Projectes** (.vtracklist): desen l'ordre, els títols i les pauses. Guarden camins relatius, així que es pot moure la carpeta del disc a un altre ordinador.

## Generar l'executable (`VinylTracklist.exe`)

### Opció A — GitHub (no cal instal·lar res)

1. Puja el contingut d'aquesta carpeta al repositori `Fobdbat/VinylTracklist` (a la web: *Add file › Upload files* i arrossega-hi tots els fitxers i carpetes, inclosa `.github`).
2. GitHub compila sol: pestanya **Actions** › l'execució més recent (uns 5 minuts).
3. A baix de tot, a **Artifacts**, descarrega `VinylTracklist-windows-x86` (32 bits, funciona a tots els Windows del 7 a l'11). Dins hi ha `VinylTracklist.exe`.

Cada cop que es pugi un canvi al repositori, es genera un exe nou.

### Opció B — en un PC amb Windows

1. Instal·lar **Python 3.8.10 de 32 bits** («Windows installer (32-bit)»): https://www.python.org/downloads/release/python-3810/
2. Doble clic a **`build_windows.bat`**. Passa les proves i crea **`dist\VinylTracklist.exe`**.

En tots dos casos l'exe és un sol fitxer: es copia a cada ordinador i ja funciona (no cal instal·lar Python).
Per què Python 3.8 de 32 bits: és l'última versió de Python que funciona a Windows 7, i un programa de 32 bits funciona en Windows de 32 i de 64 bits.

## Windows 7

Cal **Service Pack 1** i les actualitzacions **KB2533623** i **KB2999226** (Universal C Runtime). Un Windows 7 actualitzat ja les té. Si l'exe no arrenca i surt un error de fitxers `api-ms-win-…dll`, cal instal·lar KB2999226.

## Primer cop que s'obre

Com que l'exe no està signat digitalment, Windows 10/11 pot mostrar «Windows ha protegit l'ordinador». Cal clicar **Més informació › Executa igualment**.

## Fitxers del programa

- Configuració: `%APPDATA%\VinylTracklist\config.json`
- Errors inesperats: `%APPDATA%\VinylTracklist\errors.log`

## Estructura del codi

```
VinylTracklist.pyw          punt d'entrada
vinyltracklist/wavinfo.py   lectura de capçaleres WAV (RIFF, RF64, BW64, PCM, float, extensible)
vinyltracklist/model.py     cares, temes, ordenació, pauses, temps i avisos
vinyltracklist/i18n.py      textos ca / es / en
vinyltracklist/config.py    configuració persistent
vinyltracklist/export/      informes: dades comunes, TXT, Word i PDF (sense dependències externes)
vinyltracklist/ui/          interfície (tkinter): Tracklist, Informe (vista prèvia), configuració
tests/                      proves automàtiques
```

Només depèn de la biblioteca estàndard de Python, més `tkinterdnd2` (per arrossegar des de l'Explorador).

## Proves

```
python -m unittest discover -s tests -p "test_*.py"
```
