# Cryptmorrow 01 – Il motore a tile

Analisi del codice di [game/src/main.asm](game/src/main.asm) e dei sorgenti
collegati, con una descrizione dettagliata, istruzione per istruzione,
dell'algoritmo che disegna una stanza attraverso le metatile.

---

## 1. Struttura del programma

[main.asm](game/src/main.asm) è l'unico file da assemblare (sintassi 64tass) e
include tutti gli altri:

| File | Ruolo |
|---|---|
| [memory.asm](game/src/memory.asm) | Mappa di memoria e variabili in zero page |
| `assets/generated/dungeon.asm` | Costanti generate (es. `START_ROOM = 1`) |
| [room.asm](game/src/room.asm) | Il motore a tile: pulizia dello schermo, `draw_room`, `draw_half`, torce |
| [text.asm](game/src/text.asm) | Stampa del testo nel bitmap (nome della stanza) |
| [world.asm](game/src/world.asm) | Stato del gioco, indirizzo della stanza, palette della zona |
| [data.asm](game/src/data.asm) | Inclusione dei binari generati (tile, attributi, font, stanze, colori) |

### 1.1 Inizializzazione ([main.asm:19-62](game/src/main.asm#L19-L62))

1. Disattiva gli interrupt (`sei`), azzera lo stack e scrive `$36` in `$01`.
   In questo modo la ROM BASIC sparisce e a `$A000-$BFFF` resta visibile la
   RAM, dove stanno `ROOM_DATA` e `ZONE_COLOURS`. KERNAL e I/O restano attivi.
2. Spegne gli IRQ di CIA e VIC, mette bordo e sfondo a nero e inizializza
   `colour_zone = $FF`, cioè "nessuna palette caricata".
3. Spegne il display con `$D011 = $0B`, così il disegno non si vede mentre
   avviene.
4. Configura il VIC-II:
   - `$DD00`: bit = `%10` seleziona il **bank 1, `$4000-$7FFF`**, che non ha
     l'ombra della Char ROM.
   - `$D018 = $18`: screen RAM a `$4400`, bitmap a `$6000`.
   - `$D016 = $18`: modo **multicolor**, 40 colonne.
5. Chiama in sequenza `clear_screen`, `init_game` (stanza iniziale) ed
   `enter_room`.

### 1.2 Loop principale ([main.asm:64-95](game/src/main.asm#L64-L95))

- `wait_frame` aspetta il bordo inferiore PAL guardando il 9° bit del raster
  (bit 7 di `$D011`). Prima attende che diventi 1, poi che torni a 0: si
  sincronizza così con l'inizio del frame senza usare interrupt.
- Ogni 8 frame calcola `torch_phase = (frame/8) mod 4` e chiama
  `animate_torches`. L'unica cosa animata, per ora, sono le fiamme delle torce.

---

## 2. Modello grafico

### 2.1 Il bitmap multicolor

Il gioco usa il **bitmap multicolor**: 40×25 celle, ciascuna di 4×8 pixel
logici in 8 byte. Ogni cella ha tre colori propri più lo sfondo:

| Codice pixel | Origine del colore |
|---|---|
| `00` | `$D021`, nero |
| `01` | screen RAM, nibble alto |
| `10` | screen RAM, nibble basso |
| `11` | Color RAM `$D800` |

Disegnare una cella significa quindi scrivere in **tre aree**: 8 byte di
bitmap, 1 byte di screen RAM e 1 byte di Color RAM. Il motore ne aggiorna anche
una quarta, la mappa di calpestabilità `SOLID_MAP`.

Nel bitmap la cella (riga `r`, colonna `c`) occupa 8 byte consecutivi, uno per
ogni riga di pixel:

```
indirizzo cella = BITMAP + r*320 + c*8
byte y della cella (riga di pixel y=0..7) = indirizzo cella + y
```

Una riga di 40 celle è quindi lunga 40×8 = **320 byte**, e due celle affiancate
sono **16 byte consecutivi**. Tutto l'algoritmo si basa su questo fatto.

Screen RAM, Color RAM e `SOLID_MAP` hanno invece **un byte per cella**:
indirizzo = base + r*40 + c.

### 2.2 Le metatile

Una **metatile** è 2×2 celle, cioè 16×16 pixel a schermo. Una stanza è una
griglia di **20×10 metatile**, quindi 40×20 celle, disegnata dalla riga di
celle 3 alla 22. La riga 24 contiene il nome della stanza.

Il catalogo (fino a 128 metatile) è diviso in tabelle parallele:

```
TILE_BITMAP $8000   32 byte per tile: TL(8) TR(8) BL(8) BR(8)
TILE_SCR_L  $9000   byte screen RAM, cella sinistra  ┐ indice id     = metà superiore
TILE_SCR_R  $9100   byte screen RAM, cella destra    │ indice id+128 = metà inferiore
TILE_COL_L  $9200   Color RAM, cella sinistra        │
TILE_COL_R  $9300   Color RAM, cella destra          ┘
TILE_ATTR   $9400   bit 0-3: solido TL/TR/BL/BR; bit 4-6: tipo
```

Due scelte di layout rendono veloce il disegno:

1. **L'ordine TL, TR, BL, BR nel bitmap della tile.** Nel bitmap del C64 due
   celle adiacenti sulla stessa riga sono 8 byte consecutive l'una dopo
   l'altra. Quindi i 16 byte TL+TR (o BL+BR) di una tile si copiano **in
   blocco** in 16 byte consecutivi dello schermo.
2. **Le tabelle colori indicizzate con `id | half`**, dove `half` vale `$00` o
   `$80`. Con un solo `ORA` si passa dalla metà superiore a quella inferiore, e
   l'indice resta in X per tutti e quattro gli accessi `TILE_xxx_L/R,x`.

Un'altra conseguenza: i **pixel** delle tile sono uguali in tutte le zone,
mentre i **colori** stanno solo nelle quattro tabelle da 256 byte. Per
cambiare palette basta copiare 1 KB (vedi 3.3).

Il catalogo è prodotto offline da `game/assets/build_assets.py` e
`game/assets/tiles.py`, che fanno l'autotiling, eliminano i duplicati e
codificano ogni cella con `c64gfx.encode_cell`.

---

## 3. Preparazione della stanza

### 3.1 `enter_room` ([world.asm:15-28](game/src/world.asm#L15-L28))

```
display off → room_address → set_zone → draw_room → animate_torches → wait_frame → display on
```

Il display si riaccende dopo `wait_frame`, cioè all'inizio di un frame, così
non si vede mai metà immagine. A display spento non ci sono badline, quindi la
CPU ha tutti i cicli a disposizione.

### 3.2 `room_address` ([world.asm:33-42](game/src/world.asm#L33-L42))

Ogni stanza occupa una pagina di 256 byte: `ROOM_DATA + room_slot*256`.
L'indirizzo si calcola sommando `room_slot` al byte alto. Il risultato va in
due puntatori:

- `room_ptr` viene consumato da `draw_room` mentre avanza riga per riga;
- `page_ptr` resta fermo e serve per leggere i campi dell'header
  (`ROOM_ZONE` all'offset 209, `ROOM_NAME` al 228).

Layout della pagina: byte 0-199 la mappa 20×10, poi l'header (oggetti, porta,
zona) e infine la stringa del nome.

### 3.3 `set_zone` ([world.asm:50-77](game/src/world.asm#L50-L77))

Legge la zona della stanza (0 = atrio, 1-3 = zone A-C). Se è la stessa già
caricata (`colour_zone`), esce subito. Altrimenti copia 4 pagine da
`ZONE_COLOURS + zona*$400` in `TILE_SCR_L…TILE_COL_R`. Il `.cerror` alla
riga 49 garantisce che le quattro tabelle siano contigue, così basta un loop di
4×256 byte.

Le palette sono generate offline da `tiles.py` (`ZONE_PALETTES` /
`recoloured`), che sostituisce i colori nibble per nibble. Esempio: il verde
muschio dell'atrio diventa grigio nella zona A.

### 3.4 `clear_screen` ([room.asm:34-56](game/src/room.asm#L34-L56))

Usa `fill_pages`, che riempie X pagine intere con A (tutte le aree partono da
un confine di pagina):

- bitmap `$6000-$7FFF`, 32 pagine, a 0;
- screen RAM e Color RAM, 4 pagine ciascuna, a 0;
- `SOLID_MAP`, 4 pagine, a **1**: ogni cella è muro finché una stanza non la
  sovrascrive. Le righe fuori dalla mappa (0-2 e 23-24) restano quindi solide.

---

## 4. `draw_room`: preparazione dei puntatori ([room.asm:66-87](game/src/room.asm#L66-L87))

```asm
draw_room:
        lda #0
        sta torch_count          ; lista torce vuota
        sta half                 ; $00 = si parte dalle celle superiori
```

`half` è il selettore della metà. Vale solo `$00` o `$80`, perché il bit 7 si
testa gratis con `bit`/`bmi`/`bpl` e si può mettere in OR con un id < 128.

```asm
        lda #<(BITMAP + FIRST_ROW * 320)    ; $63C0
        sta bmp_ptr
        lda #>(BITMAP + FIRST_ROW * 320)
        sta bmp_ptr+1
        ... scr_ptr = SCREEN    + 3*40 = $4478
        ... col_ptr = COLOR_RAM + 3*40 = $D878
        ... sol_ptr = SOLID_MAP + 3*40 = $9878
        lda #CELL_ROWS                       ; 20
        sta rows_left
```

I quattro puntatori in zero page indicano la **prima cella della riga 3** in
ciascuna delle quattro aree. Le espressioni `<(…)` e `>(…)` le calcola
l'assembler, quindi a runtime ci sono solo `lda #imm / sta zp`.

Stato all'ingresso del ciclo:

| Variabile | Valore | Significato |
|---|---|---|
| `room_ptr` | `$Ann00` | inizio della mappa (pagina della stanza) |
| `half` | `$00` | metà superiore |
| `bmp_ptr` | `$63C0` | bitmap, riga di celle 3, colonna 0 |
| `scr_ptr` / `col_ptr` / `sol_ptr` | `$4478` / `$D878` / `$9878` | riga 3, colonna 0 |
| `rows_left` | 20 | righe di celle da disegnare |

---

## 5. Il ciclo esterno: righe di celle ([room.asm:89-131](game/src/room.asm#L89-L131))

L'idea chiave: **ogni riga della mappa si legge due volte**. La prima passata
disegna la metà superiore di ogni metatile (riga di celle pari), la seconda la
metà inferiore (riga dispari). Così il disegno procede **una riga di celle
alla volta, in ordine lineare di memoria**, e i puntatori avanzano sempre in un
solo verso.

```asm
draw_cell_row:
        lda #0
        sta map_col              ; indice nella riga della mappa (0..19)
        sta cell_col             ; indice di colonna di cella (0..38, passo 2)
```

Due contatori distinti perché ogni metatile occupa 2 colonne di celle:
`map_col` scorre la mappa, `cell_col` scorre screen/color/solid. Il bitmap
invece non usa indici: `bmp_ptr` viene spostato direttamente.

### 5.1 Il ciclo interno: 20 metatile

```asm
draw_tile:
        ldy map_col
        lda (room_ptr),y         ; A = id della metatile in (riga mappa, map_col)
        jsr draw_half            ; disegna 2 celle, cell_col += 2
```

`room_ptr` punta sempre all'inizio della riga **corrente** della mappa, quindi
`(room_ptr),y` con Y = colonna restituisce l'id.

```asm
        clc
        lda bmp_ptr
        adc #16                  ; due celle = 16 byte di bitmap
        sta bmp_ptr
        bcc same_page
        inc bmp_ptr+1            ; riporto nel byte alto
same_page:
```

Classica somma a 16 bit di una costante a 8 bit. Il `bcc` salta l'`inc` nel
caso più comune, cioè quando non c'è attraversamento di pagina.

```asm
        inc map_col
        lda map_col
        cmp #MAP_WIDTH           ; 20
        bne draw_tile
```

Fine del ciclo interno dopo 20 metatile.

### 5.2 Fine di una riga di celle

A questo punto `bmp_ptr` è avanzato di 20 × 16 = **320** byte e punta già alla
prima cella della riga successiva: il bitmap non va riallineato.

Gli altri tre puntatori sono rimasti fermi, perché `draw_half` scrive con
l'indice `cell_col` senza toccarli. Vanno quindi spostati di una riga, cioè di
40 byte:

```asm
        ldx #scr_ptr             ; X = indirizzo in ZP del puntatore ($14)
        jsr down_one_row
        ldx #col_ptr             ; $16
        jsr down_one_row
        ldx #sol_ptr             ; $18
        jsr down_one_row
```

`down_one_row` ([room.asm:261-269](game/src/room.asm#L261-L269)) è una
subroutine "per riferimento":

```asm
down_one_row:
        clc
        lda 0,x                  ; byte basso del puntatore il cui indirizzo è X
        adc #40
        sta 0,x
        bcc row_moved
        inc 1,x                  ; byte alto
row_moved:
        rts
```

`lda 0,x` è l'indirizzamento **zero page indicizzato**: legge dall'indirizzo
`$00 + X`. Passando in X l'indirizzo del puntatore, la stessa routine
incrementa uno qualunque dei tre puntatori a 16 bit. Su un 6502 è l'equivalente
di passare un puntatore a puntatore.

### 5.3 Alternanza delle metà e avanzamento nella mappa

```asm
        lda half
        eor #$80                 ; $00 → $80 → $00 → ...
        sta half
        bne next_cell_row        ; ora vale $80: la metà inferiore non è ancora fatta
```

- Se `half` è appena diventata `$80`, abbiamo disegnato solo le metà
  superiori. Si salta a `next_cell_row` **senza toccare `room_ptr`**, così la
  stessa riga della mappa viene riletta per le metà inferiori.
- Se `half` è tornata `$00`, entrambe le metà sono fatte e si passa alla riga
  successiva della mappa:

```asm
        clc
        lda room_ptr
        adc #MAP_WIDTH           ; +20 byte
        sta room_ptr
        bcc next_cell_row
        inc room_ptr+1           ; mai eseguito in pratica: 10×20 = 200 < 256
next_cell_row:
        dec rows_left
        beq map_complete
        jmp draw_cell_row
```

Sequenza completa:

| `rows_left` | riga di celle | `half` | riga mappa letta |
|---|---|---|---|
| 20 | 3 | `$00` | 0 (metà superiori) |
| 19 | 4 | `$80` | 0 (metà inferiori) |
| 18 | 5 | `$00` | 1 |
| 17 | 6 | `$80` | 1 |
| … | … | … | … |
| 1 | 22 | `$80` | 9 |

Schema in memoria per una riga della mappa:

```
mappa  [ t0 ][ t1 ][ t2 ] ... [t19]
          │     │
  riga 2k │TL TR│TL TR│ ...         ← half = $00, bitmap: 16 byte per tile
  riga 2k+1│BL BR│BL BR│ ...        ← half = $80, stessa riga della mappa riletta
```

### 5.4 Il nome della stanza

```asm
map_complete:
        lda #ROOM_NAME           ; 228
        sta text_ptr
        lda room_ptr+1           ; stessa pagina della stanza
        sta text_ptr+1
        jsr clear_name_row
        jmp print_text           ; tail call: l'rts di print_text torna al chiamante
```

Alla fine `room_ptr` vale `pagina + 200`. Poiché 200 < 256 siamo ancora nella
stessa pagina, quindi il nome si trova a `(room_ptr+1):ROOM_NAME` senza
ricalcoli. Il `jmp` al posto di `jsr` + `rts` risparmia 6+6 cicli e 1 byte di
stack.

---

## 6. `draw_half`: mezza metatile ([room.asm:147-258](game/src/room.asm#L147-L258))

**Ingresso:** A = id (0-127), `half`, `bmp_ptr`, `scr_ptr`, `col_ptr`,
`sol_ptr`, `cell_col`.
**Uscita:** 2 celle disegnate nelle 4 aree e `cell_col` aumentato di 2.
`bmp_ptr` **non** viene modificato: lo sposta il chiamante.

### 6.1 Indici di partenza

```asm
        sta tile_id              ; conserva l'id
        tay                      ; Y = id
        lda TILE_ATTR,y          ; attributi della metatile
        sta attr_bits
        tya
        ora half                 ; id | $00  oppure  id | $80
        tax                      ; X = indice nelle tabelle colori
```

X resta intatto fino alla fine della routine e serve nei 4 accessi alle tabelle
colori (6.7). Il bit 7 di `id | half` sceglie la metà: le tabelle hanno 256
voci, le prime 128 per le celle superiori e le seconde 128 per quelle
inferiori.

### 6.2 Indirizzo sorgente del bitmap: `TILE_BITMAP + id*32 (+16)`

```asm
        lda tile_id
        lsr a
        lsr a
        lsr a                    ; A = id >> 3
        clc
        adc #>TILE_BITMAP        ; + $80
        sta src_ptr+1
        lda tile_id
        asl a
        asl a
        asl a
        asl a
        asl a                    ; A = (id << 5) & $FF  → bit 0-4 sempre a 0
        bit half                 ; N = bit 7 di half
        bpl source_ready         ; metà superiore: offset 0
        ora #16                  ; metà inferiore: +16 (bit 4 libero, nessun riporto)
source_ready:
        sta src_ptr
```

#### 6.2.1 Che cosa si calcola

Ogni metatile occupa **32 byte** in `TILE_BITMAP` ($8000): 4 celle (TL, TR,
BL, BR) da 8 byte ciascuna.

```
tile id → $8000 + id*32
          +$00 .. +$07   TL ┐ metà superiore (16 byte)
          +$08 .. +$0F   TR ┘
          +$10 .. +$17   BL ┐ metà inferiore (16 byte)
          +$18 .. +$1F   BR ┘
```

L'indirizzo che serve è:

```
src = $8000 + id*32          se half = $00 (metà superiore)
src = $8000 + id*32 + 16     se half = $80 (metà inferiore)
```

Il 6502 non ha un'istruzione di moltiplicazione e lavora a 8 bit, mentre
`id*32` arriva a 127×32 = 4064 (`$0FE0`), che non sta in un byte. Il risultato
va quindi costruito come **due byte separati**: alto (`src_ptr+1`) e basso
(`src_ptr`).

#### 6.2.2 L'idea intuitiva: pagine da 8 tile

Una pagina è lunga 256 byte, e 256 / 32 = **8 tile per pagina**. Quindi:

- **la pagina** in cui sta la tile (byte alto) = `id / 8`
- **la posizione dentro la pagina** (byte basso) = `(id mod 8) * 32`

```
pagina $80: tile  0- 7    pagina $84: tile 32-39   ...   pagina $8F: tile 120-127
pagina $81: tile  8-15    pagina $85: tile 40-47
...

dentro una pagina:
id mod 8 :   0    1    2    3    4    5    6    7
offset   :  $00  $20  $40  $60  $80  $A0  $C0  $E0
```

Il codice calcola proprio queste due cose: tre `lsr` danno `id / 8` e cinque
`asl` danno `(id mod 8) * 32`.

#### 6.2.3 La stessa cosa vista in binario

L'id ha 7 bit significativi (0-127): `0 b6 b5 b4 b3 b2 b1 b0`.

Moltiplicare per 32 = 2⁵ significa **spostare a sinistra di 5 posizioni**:

```
id*32 =  0000 b6b5b4b3 | b2b1b0 00000
         └─ byte alto ─┘ └─ byte basso ─┘
```

Il taglio fra i due byte cade fra `b3` e `b2`:

| Byte | Bit | Si ottiene con |
|---|---|---|
| alto | `0 0 0 0 b6 b5 b4 b3` | id spostato a **destra** di 3 (`id >> 3`) |
| basso | `b2 b1 b0 0 0 0 0 0` | id spostato a **sinistra** di 5, perdendo i bit che escono (`id << 5`) |

È la stessa divisione in pagina e offset del punto 6.2.2, letta sui bit.

#### 6.2.4 Traccia istruzione per istruzione con id = `$25` (37)

`$25` = `%0010_0101`. Risultato atteso: `$8000 + 37*32 = $8000 + $04A0 = $84A0`.

**Byte alto**

| Istruzione | A | C | Note |
|---|---|---|---|
| `lda tile_id` | `0010 0101` | – | A = $25 |
| `lsr a` | `0001 0010` | 1 | esce b0 |
| `lsr a` | `0000 1001` | 0 | esce b1 |
| `lsr a` | `0000 0100` | **1** | esce b2: A = 4 = 37/8 |
| `clc` | `0000 0100` | 0 | **indispensabile**, vedi sotto |
| `adc #>TILE_BITMAP` | `1000 0100` | 0 | 4 + $80 = **$84** |
| `sta src_ptr+1` | | | |

- **Perché serve `clc`.** `adc` somma anche il carry, e dopo il terzo `lsr` il
  carry contiene `b2`, che per $25 vale 1. Senza `clc` il risultato sarebbe
  $80 + 4 + 1 = **$85**: una pagina sbagliata, con la grafica di un'altra tile.
- **Perché qui non c'è riporto in uscita.** `id >> 3` vale al massimo 15,
  quindi $80 + 15 = $8F: si resta sempre dentro `$8000-$8FFF`.
- **Perché basta sommare al byte alto.** `TILE_BITMAP` = `$8000` ha byte basso
  `$00`. Se la tabella fosse a `$8010`, servirebbe una somma a 16 bit con
  propagazione del carry. Questo è il motivo per cui le tabelle in
  [memory.asm](game/src/memory.asm) sono allineate a pagina.

**Byte basso**

| Istruzione | A | C (bit uscito) | Note |
|---|---|---|---|
| `lda tile_id` | `0010 0101` | – | si riparte dall'id originale |
| `asl a` | `0100 1010` | 0 | esce b7 (sempre 0) |
| `asl a` | `1001 0100` | 0 | esce b6 |
| `asl a` | `0010 1000` | 1 | esce b5 |
| `asl a` | `0101 0000` | 0 | esce b4 |
| `asl a` | `1010 0000` | 0 | esce b3: A = **$A0** |

I bit `b6..b3` escono a sinistra e si perdono, ma non è un errore: sono
esattamente quelli già messi nel byte alto. Restano `b2 b1 b0` (`101`) nei 3
bit alti, seguiti da cinque zeri. Il controllo torna: 37 mod 8 = 5 e
5 × 32 = 160 = $A0.

**Scelta della metà**

```asm
        bit half                 ; N = bit 7 di half
        bpl source_ready         ; N=0 → metà superiore: A resta $A0
        ora #16                  ; N=1 → metà inferiore: A = $A0 | $10 = $B0
source_ready:
        sta src_ptr
```

*Che cosa fa `bit`.* `bit half` legge la memoria e imposta tre flag, **senza
modificare A**:

- N ← bit 7 di `half`
- V ← bit 6 di `half`
- Z ← (A AND `half`) == 0

Qui conta solo N: con `half` = $00 vale 0, con `half` = $80 vale 1. Il punto
chiave è che A contiene ancora il byte basso appena calcolato. Con
`lda half / bmi …` quel valore andrebbe perso, e ricaricarlo costerebbe
istruzioni e cicli. Per questo `half` usa proprio il bit 7: si testa con `bit`
"gratis" e senza toccare i registri.

*Perché `ora #16` invece di `clc` + `adc #16`.* Dopo cinque `asl` i 5 bit
bassi di A sono sempre zero:

```
A      = b2 b1 b0 0 0 0 0 0
#16    =  0  0  0 1 0 0 0 0
A | 16 = b2 b1 b0 1 0 0 0 0      ← identico ad A + 16
```

Se il bit da accendere è 0, OR e somma coincidono. In più:

- non serve `clc` (2 cicli e 1 byte risparmiati);
- non c'è mai riporto verso il byte alto: il massimo è $E0 | $10 = $F0. In
  termini di layout, ogni tile è allineata a 32 byte, quindi aggiungere 16
  resta sempre dentro la stessa tile e la stessa pagina.

**Risultato**

| `half` | `src_ptr+1` | `src_ptr` | Puntatore | Contenuto |
|---|---|---|---|---|
| $00 | $84 | $A0 | **$84A0** | TL ($84A0-A7) + TR ($84A8-AF) |
| $80 | $84 | $B0 | **$84B0** | BL ($84B0-B7) + BR ($84B8-BF) |

`src_ptr` è un puntatore in zero page usabile da `lda (src_ptr),y`, che serve
subito dopo nella copia srotolata dei 16 byte (6.3).

#### 6.2.5 Costo e alternative

| Parte | Cicli |
|---|---|
| byte alto: `lda zp` 3 + 3×`lsr` 6 + `clc` 2 + `adc #` 2 + `sta zp` 3 | 16 |
| byte basso: `lda zp` 3 + 5×`asl` 10 + `bit zp` 3 + `bpl` 2/3 + `ora #` 0/2 + `sta zp` 3 | 22-23 |
| **Totale** | **~39 cicli** |

Su 400 mezze metatile fanno circa 15.600 cicli, poco meno di un frame PAL.

Le alternative possibili:

- **Moltiplicazione generica a 16 bit** (`asl` sul byte basso + `rol`
  sull'alto, 5 volte): circa 35 cicli solo per lo shift, poi la somma della
  base e la gestione della metà. È più lenta e più lunga.
- **Tabelle precalcolate** `tile_lo[id]` / `tile_hi[id]` (128 + 128 byte):
  `lda tile_hi,y` / `sta` / `lda tile_lo,y` / `ora` …, circa 20 cicli.
  Guadagna una ventina di cicli per chiamata (circa 8.000 per stanza) al prezzo
  di 256 byte di RAM.
- Il valore calcolato per la metà superiore si potrebbe riusare per la
  inferiore, ma nell'algoritmo attuale le due metà della stessa tile vengono
  disegnate in passate diverse (righe di celle diverse), quindi il calcolo si
  ripete.

Lo shift è un compromesso ragionevole: zero memoria aggiuntiva e un costo
piccolo rispetto ai 208 cicli della copia del bitmap che segue.

### 6.3 Copia dei 16 byte di bitmap, srotolata

```asm
        .for offset = 15, offset >= 0, offset -= 1
        ldy #offset
        lda (src_ptr),y
        sta (bmp_ptr),y
        .next
```

L'assembler genera 16 terne:

```asm
        ldy #15 / lda (src_ptr),y / sta (bmp_ptr),y
        ldy #14 / lda (src_ptr),y / sta (bmp_ptr),y
        ...
        ldy #0  / lda (src_ptr),y / sta (bmp_ptr),y
```

- Byte 0-7 della sorgente → cella sinistra (TL o BL), 8 righe di pixel.
- Byte 8-15 → cella destra (TR o BR).

Poiché sia la tile che lo schermo hanno le celle affiancate in 16 byte
consecutivi, la copia è un semplice `memcpy` di 16 byte.

Costo: `ldy #` 2 + `lda (zp),y` 5 + `sta (zp),y` 6 = **13 cicli/byte**. Con un
loop (`lda`, `sta`, `dey`, `bpl`) sarebbero 16. `sta (zp),y` costa sempre 6
cicli; `lda (zp),y` costa 5, più 1 se attraversa una pagina. Qui non succede
mai: `src_ptr` è un multiplo di 16, e `bmp_ptr` è sempre `$63C0 + 16k`, quindi
anche lui multiplo di 16.

### 6.4 Registrazione delle torce (solo metà superiore)

```asm
        bit half
        bmi torch_checked        ; metà inferiore: niente fiamme, salta
        lda attr_bits
        and #TYPE_MASK           ; %0111_0000: solo il tipo
        beq torch_checked        ; tipo 0 = tile normale (il caso più frequente)
        cmp #TORCH_LEFT          ; 1<<4 = $10
        beq flame_in_left_cell
        cmp #TORCH_RIGHT         ; 2<<4 = $20
        bne torch_checked        ; altri tipi (uscita, porta): niente fiamma
        lda #8                   ; fiamma nella cella destra: +8 byte
        jmp add_torch
flame_in_left_cell:
        lda #0                   ; fiamma nella cella sinistra: +0
add_torch:
        ldy torch_count
        cpy #MAX_TORCHES         ; 6
        bcs torch_checked        ; lista piena (C=1 se Y >= 6)
        clc
        adc bmp_ptr              ; A = offset + byte basso
        sta torch_lo,y
        lda bmp_ptr+1
        adc #0                   ; propaga il riporto
        sta torch_hi,y
        inc torch_count
torch_checked:
```

La lista salvata contiene l'indirizzo **assoluto nel bitmap** della cella con
la fiamma. `animate_torches` dovrà solo copiarci 8 byte, senza consultare la
mappa né rifare calcoli.

Il test di tipo `beq` dopo `and` esce il prima possibile per le tile normali:
il percorso più frequente costa circa 13 cicli.

### 6.5 Valore di "solido": muro o porta

```asm
        ldy #WALL_CELL           ; 1
        lda attr_bits
        and #TYPE_MASK
        cmp #TYPE_DOOR           ; 4<<4 = $40
        bne cell_value_ready
        ldy #DOOR_CELL           ; 2
cell_value_ready:
        sty solid_value
```

Y viene preimpostato e sovrascritto solo nel caso raro: è l'idioma "valore di
default + eccezione" che evita un salto in avanti.

### 6.6 Estrazione dei bit solidi della metà

Gli attributi hanno i bit 0-3 = solidità di TL, TR, BL, BR.

```asm
        lda attr_bits
        bit half
        bpl solid_ready          ; metà superiore: TL in bit 0, TR in bit 1
        lsr a
        lsr a                    ; metà inferiore: BL → bit 0, BR → bit 1
solid_ready:
        sta solid_bits
```

Dopo questo passo, in entrambi i casi **bit 0 = cella sinistra e bit 1 = cella
destra**. Gli altri bit (tipo, ecc.) restano in `solid_bits` ma vengono
ignorati, perché se ne leggono solo due.

### 6.7 Colori e calpestabilità delle due celle

```asm
        ldy cell_col             ; Y = colonna della cella sinistra
        lda TILE_SCR_L,x         ; nibble alto = colore 01, basso = colore 10
        sta (scr_ptr),y
        lda TILE_COL_L,x         ; colore 11
        sta (col_ptr),y
        lda #0                   ; default: calpestabile
        lsr solid_bits           ; bit 0 → Carry, e solid_bits scorre a destra
        bcc left_cell_ready
        lda solid_value          ; solido: 1 muro, 2 porta
left_cell_ready:
        sta (sol_ptr),y

        iny                      ; cella destra
        lda TILE_SCR_R,x
        sta (scr_ptr),y
        lda TILE_COL_R,x
        sta (col_ptr),y
        lda #0
        lsr solid_bits           ; ex bit 1 → Carry
        bcc right_cell_ready
        lda solid_value
right_cell_ready:
        sta (sol_ptr),y

        iny
        sty cell_col             ; cell_col += 2
        rts
```

Punti da notare:

- **`lsr` in memoria come estrattore di bit.** Ogni `lsr solid_bits` mette nel
  carry il bit meno significativo e fa scorrere gli altri. Due `lsr` di seguito
  leggono il bit della cella sinistra e poi quello della destra, senza maschere
  né registri in più.
- **Lo stesso Y indicizza tre aree diverse.** `scr_ptr`, `col_ptr` e `sol_ptr`
  puntano all'inizio della stessa riga di celle in tre zone di memoria, quindi
  `(ptr),y` con lo stesso Y raggiunge la stessa cella in tutte e tre.
- **X fisso per le tabelle colori.** `TILE_SCR_L,x` è indirizzamento assoluto
  indicizzato (4 cicli); `id|half` è stato calcolato una sola volta.
- Le scritture in Color RAM (`$D878…`) funzionano perché `$01 = $36` tiene
  visibile l'I/O. La Color RAM è a 4 bit, e il nibble alto scritto viene
  ignorato.

---

## 7. Esempio numerico completo

Mettiamo che la mappa della stanza abbia, alla riga 0 e colonna 1, la metatile
**id = 37 (`$25`)** con `attr = %0001_0011`: tipo `TORCH_LEFT` e solidità
`SOLID_TOP` (TL e TR solide, BL e BR libere).

### Passata 1: riga di celle 3, `half = $00`, `map_col = 1`

| Passo | Calcolo | Risultato |
|---|---|---|
| `bmp_ptr` | `$63C0 + 1*16` | `$63D0` |
| `cell_col` | 2 (dopo la tile 0) | 2 |
| X | `$25 \| $00` | `$25` |
| `src_ptr+1` | `$80 + ($25>>3 = 4)` | `$84` |
| `src_ptr` | `($25<<5) & $FF = $4A0 & $FF` | `$A0` → **`$84A0`** = `$8000 + 37*32` ✓ |
| copia | `$84A0-$84AF` → `$63D0-$63DF` | celle (3,2) e (3,3) |
| torcia | tipo `$10` = `TORCH_LEFT` → offset 0 | `torch_lo/hi[0] = $63D0` |
| `solid_value` | tipo ≠ `$40` | 1 |
| `solid_bits` | `%0001_0011` (nessuno shift) | bit0=1, bit1=1 |
| screen | `$4478+2 ← TILE_SCR_L[$25]`, `$4478+3 ← TILE_SCR_R[$25]` | |
| color | `$D878+2 ← TILE_COL_L[$25]`, `$D878+3 ← TILE_COL_R[$25]` | |
| solid | `$9878+2 ← 1`, `$9878+3 ← 1` | entrambe muro |

Verifica: la cella (3,2) nel bitmap è
`$6000 + 3*320 + 2*8 = $6000 + $3C0 + $10 = $63D0` ✓.

### Passata 2: riga di celle 4, `half = $80`, `map_col = 1` (stessa riga della mappa)

| Passo | Calcolo | Risultato |
|---|---|---|
| `bmp_ptr` | `$6500 + 16` (`$6500` = `$63C0 + 320`) | `$6510` |
| X | `$25 \| $80` | `$A5`: seconda metà delle tabelle colori |
| `src_ptr` | `$A0 \| 16` | **`$84B0`**: byte BL+BR della tile |
| torcia | `bit half` → N=1 | saltata |
| `solid_bits` | `%0001_0011 >> 2` | `%0000_0100` → bit0=0, bit1=0 |
| solid | `$98A0+2 ← 0`, `$98A0+3 ← 0` | calpestabili |

Quando si attivano le torce, `animate_torches` copia 8 byte da
`FLAMES + phase*8` a `$63D0`, cioè proprio la cella TL della torcia.

---

## 8. Stima dei cicli

Conteggio fatto sul codice a mano, non misurato in emulatore:

| Blocco di `draw_half` | Cicli circa |
|---|---|
| `jsr` + indici (6.1) | ~25 |
| sorgente del bitmap (6.2) | ~40 |
| copia srotolata (6.3) | 16 × 13 = **208** |
| controllo torcia (6.4), tile normale | ~13 |
| `solid_value` (6.5) | ~15 |
| `solid_bits` (6.6) | ~12 |
| colori + solidità di 2 celle (6.7) + `rts` | ~90 |
| **Totale `draw_half`** | **~400** |
| più il ciclo `draw_tile` (lettura id, `bmp_ptr += 16`, contatori) | ~35 |

Per 400 mezze-metatile (20 tile × 20 righe di celle) servono circa
**175.000 cicli**. Un frame PAL a display spento (niente badline) ne ha
63 × 312 = 19.656, quindi il disegno dura **circa 9 frame, ~0,18 s**.

La copia del bitmap pesa circa metà del tempo totale. È il motivo per cui è
l'unica parte srotolata: lì il risparmio di 3 cicli per byte vale circa 19.000
cicli per stanza, quasi un frame.

---

## 9. Testo e torce: il disegno "a cella singola"

### 9.1 `print_text` ([text.asm:13-96](game/src/text.asm#L13-L96))

Formato della stringa: `colonna, riga, colore, codici glifo…, $FF`.

- Calcola gli indirizzi di partenza con le tabelle precalcolate
  `screen_rows_*` (riga×40) e `bitmap_rows_*` (riga×320), più colonna e
  colonna×8.
- Per ogni carattere: `glyph = FONT + codice*8`, copia di 8 byte nella cella,
  poi `screen = colore<<4`.
- I glifi usano solo il codice pixel `01`, quindi basta il nibble alto della
  screen RAM e la Color RAM non serve.

### 9.2 `animate_torches` ([room.asm:294-322](game/src/room.asm#L294-L322))

`flame_src = FLAMES + torch_phase*8`. Per ogni torcia registrata copia gli 8
byte del fotogramma nella cella della fiamma. I colori di quella cella sono
fissati in fase di build (`FLAME_PALETTE` rosso/arancio/giallo, con il
parametro `forced` di `encode_cell`). I 4 fotogrammi quindi condividono gli
stessi colori e serve riscrivere **solo il bitmap**, non la screen RAM né la
Color RAM.

---

## 10. Schema riassuntivo del flusso

```
draw_room
 ├─ inizializza 4 puntatori alla riga 3, half=$00, rows_left=20
 └─ for rows_left = 20..1                          ← una riga di celle
     ├─ map_col = cell_col = 0
     ├─ for map_col = 0..19                        ← una metatile
     │   ├─ A = (room_ptr)[map_col]
     │   ├─ draw_half
     │   │   ├─ X = id|half ; src = $8000 + id*32 (+16)
     │   │   ├─ 16 × (ldy/lda/sta)                 → bitmap
     │   │   ├─ [solo half=$00] torcia? → torch_lo/hi
     │   │   ├─ solid_value = porta ? 2 : 1
     │   │   ├─ solid_bits = attr (>>2 se half=$80)
     │   │   └─ 2 × (scr, col, sol)[cell_col++]    → screen/Color RAM/SOLID_MAP
     │   └─ bmp_ptr += 16
     ├─ scr/col/sol_ptr += 40                       (bmp_ptr è già +320)
     ├─ half ^= $80 ; if half==0 → room_ptr += 20
 └─ nome: text_ptr = pagina:228 → clear_name_row → print_text
```

### In sintesi

1. **Catalogo precompilato** di metatile 2×2. Pixel, colori e attributi stanno
   in tabelle separate, preparate offline dal builder Python (autotiling e
   deduplica).
2. **La palette della zona** si cambia copiando 1 KB di tabelle colori, e solo
   quando la zona cambia.
3. **Scansione per righe di celle**: ogni riga della mappa si percorre due
   volte (`half = $00` e poi `$80`), quindi tutti i puntatori di destinazione
   avanzano in modo lineare.
4. **Per ogni mezza metatile**: copia srotolata di 16 byte di bitmap, 2 byte di
   screen RAM, 2 di Color RAM e 2 di `SOLID_MAP`.
5. **Aritmetica che torna da sola**: 20×16 = 320 byte, quindi a fine riga il
   bitmap non va riallineato; `id|$80` seleziona la metà inferiore; `id>>3` /
   `id<<5` sostituiscono la moltiplicazione per 32.
6. **Effetti collaterali utili**: la lista delle celle-fiamma per l'animazione
   e la mappa di collisione con muri (1) e porte (2), entrambe prodotte nella
   stessa passata.
7. **Senza tearing**: tutto si disegna a display spento e lo schermo si
   riaccende sincronizzato al frame.
