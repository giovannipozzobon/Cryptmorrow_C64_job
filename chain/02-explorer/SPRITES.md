# Cryptmorrow 02 – L'esploratore: sprite, joystick e collisioni

Analisi del codice di `chain/02-explorer`, limitata a ciò che è nuovo
rispetto allo step 01. Il motore a tile, il testo e le torce sono descritti in
[../01-first-room/TILE_ENGINE.md](../01-first-room/TILE_ENGINE.md).

Gli esempi numerici sono valori reali, presi dal `cryptmorrow.prg` di questo
step e da una simulazione in Python della logica di collisione.

---

## 0. Cosa cambia rispetto allo step 01

| File | Modifica |
|---|---|
| [hero.asm](game/src/hero.asm) | **nuovo**: joystick, movimento, collisioni, animazione, posizionamento dello sprite |
| [main.asm](game/src/main.asm) | configura la CIA1, chiama `init_hero` e ogni frame `read_joystick` + `play_frame` |
| [memory.asm](game/src/memory.asm) | `SPRITE_DATA`, `SPRITE_PTRS` e 13 nuove variabili in zero page |
| [data.asm](game/src/data.asm) | include `hero.sprites` (8 fotogrammi × 64 byte) a `$4000` |
| [world.asm](game/src/world.asm) | `enter_room` chiama anche `place_hero` |
| `room.asm`, `text.asm` | identici |
| `assets/rooms/moss_gate.txt` | la torcia destra della riga 1 si sposta dalla colonna 12 alla 14 |

---

## 1. Memoria

```
VIC bank 1 ($4000-$7FFF)
$4000-$41FF  SPRITE_DATA: 8 fotogrammi × 64 byte   ← nuovo
$4200-$43FF  libero
$4400-$47E7  screen RAM (colori 01/10 del bitmap)
$47F8-$47FF  SPRITE_PTRS: puntatori degli sprite 0-7 ← nuovo
$6000-$7F3F  bitmap
```

- **I dati degli sprite devono stare nel bank del VIC.** Il VIC-II vede solo i
  16 KB del bank selezionato, quindi i fotogrammi vanno fra `$4000` e `$7FFF`.
  `SPRITE_DATA = $4000` è l'inizio del bank.
- **Il puntatore dello sprite** è un byte che vale "indirizzo / 64" relativo
  all'inizio del bank: `HERO_POINTER = ($4000 − $4000) / 64 = 0`. I fotogrammi
  sono quindi i puntatori 0-7.
- **`SPRITE_PTRS = SCREEN + $3F8 = $47F8`.** Il VIC cerca i puntatori negli
  ultimi 8 byte della screen matrix. Il bitmap usa solo 1000 byte della screen
  RAM (`$4400-$47E7`), quindi i puntatori non si sovrappongono ai colori.
- **Limite del codice.** Il controllo diventa `.cerror code_end > SPRITE_DATA`:
  il programma, che parte da `$0801`, non deve arrivare a `$4000`. Oggi finisce
  a `$0E03` (dal file `.lbl`), quindi c'è molto spazio.

`clear_screen` azzera `$4400-$47FF`, e quindi anche i puntatori, che partono
così dal fotogramma 0. `clear_name_row` si ferma a `$47E7` e non li tocca.

### Nuove variabili in zero page

| Nome | Ind. | Contenuto |
|---|---|---|
| `joy_state` | `$02` | bit `JOY_*` attivi alti |
| `hero_x` | `$03-$04` | X dello sprite sullo schermo, 16 bit (0-319) |
| `hero_y` | `$05` | Y dello sprite sullo schermo, 8 bit |
| `hero_dir` | `$06` | `DIR_DOWN` 0, `UP` 1, `LEFT` 2, `RIGHT` 3 |
| `hero_moving` | `$07` | 1 se in questo frame c'è stato almeno un passo |
| `walk_frame` | `$08` | 0/1, fotogramma della camminata |
| `walk_timer` | `$09` | frame trascorsi dall'ultimo cambio |
| `probe_x` | `$0A-$0B` | punto da testare, X a 16 bit |
| `probe_y` | `$0C` | punto da testare, Y |
| `cell_ptr` | `$0D-$0E` | riga di `SOLID_MAP` del punto |
| `step_count` | `$0F` | passi ancora da fare in questo frame |
| `hero_block` | `$3D` | cosa ha fermato l'esploratore: 0, 1 muro, 2 porta |

Le coordinate sono in **pixel dello schermo**, gli stessi del bitmap: (0, 0) è
l'angolo in alto a sinistra dell'area di 320×200. La conversione in coordinate
del VIC avviene solo in `place_hero`. Così le collisioni e la mappa di
calpestabilità usano un sistema di coordinate semplice e allineato alle celle.

---

## 2. Lo sprite dell'esploratore

### 2.1 Formato multicolor

Uno sprite hardware è 24×21 pixel, 3 byte per riga, 63 byte più un byte di
riempimento: 64. In **multicolor** ogni coppia di bit forma un pixel largo il
doppio, quindi la risoluzione logica è **12×21**.

| Codice | Carattere in `sprites.py` | Registro | Colore |
|---|---|---|---|
| `00` | `.` | – | trasparente |
| `01` | `B` | `$D025` (condiviso fra tutti gli sprite) | 9 marrone: contorno, capelli, stivali |
| `10` | `G` | `$D027` (proprio dello sprite 0) | 5 verde: tunica |
| `11` | `S` | `$D026` (condiviso) | 10 rosso chiaro: pelle |

A differenza del bitmap, dove ogni cella ha i suoi tre colori, negli sprite
**due colori sono condivisi da tutti gli sprite** e uno solo è proprio. Per
questo `sprites.py` riserva il codice 10 (`G`) al colore che cambia da sprite a
sprite: la tunica verde dell'esploratore, e nei capitoli successivi le ossa
degli scheletri o il viola dei pipistrelli.

### 2.2 Codifica (`encode_sprite`)

Ogni riga di 12 caratteri diventa 24 bit, cioè 3 byte big-endian. Alcune righe
del primo fotogramma (verso il basso, fermo):

| Riga | Disegno | Codici | Byte |
|---|---|---|---|
| 0 | `....BBBB....` | `00 00 00 00 01 01 01 01 00 00 00 00` | `00 55 00` |
| 2 | `...BSSSSB...` | `00 00 00 01 11 11 11 11 01 00 00 00` | `01 FF 40` |
| 3 | `...BS.SSB...` | `00 00 00 01 11 00 11 11 01 00 00 00` | `01 CF 40` |
| 7 | `..SGGGGGGS..` | `00 00 11 10 10 10 10 10 10 11 00 00` | `0E AA B0` |

Nel `.prg`, a `$4000`, si trova proprio `00 55 00 01 55 40 01 FF 40 01 CF 40 …`
(il punto nella riga 3 è l'occhio).

### 2.3 Gli 8 fotogrammi e il loro ordine

```python
HERO_FRAMES = HERO_DOWN + HERO_UP + HERO_LEFT + HERO_RIGHT
HERO_RIGHT  = [[row[::-1] for row in frame] for frame in HERO_LEFT]
```

| Puntatore | Indirizzo | Direzione (`hero_dir`) | `walk_frame` |
|---|---|---|---|
| 0 | `$4000` | giù (0) | 0: fermo / passo A |
| 1 | `$4040` | giù | 1: passo B |
| 2 | `$4080` | su (1) | 0 |
| 3 | `$40C0` | su | 1 |
| 4 | `$4100` | sinistra (2) | 0 |
| 5 | `$4140` | sinistra | 1 |
| 6 | `$4180` | destra (3) | 0 |
| 7 | `$41C0` | destra | 1 |

L'ordine è scelto in modo che **puntatore = `hero_dir` × 2 + `walk_frame`**. I
valori di `DIR_*` in `hero.asm` sono gli stessi dell'ordine in `sprites.py`, e
su questo si basa `animate_hero` (sezione 7).

I fotogrammi a destra sono gli specchi di quelli a sinistra, generati dal
builder: nel C64 non esiste il flip hardware degli sprite, quindi i fotogrammi
specchiati vanno comunque memorizzati.

---

## 3. Inizializzazione

### 3.1 La CIA1 ([main.asm:60-63](game/src/main.asm#L60-L63))

```asm
        lda #$ff                ; CIA1 port A: inputs, so
        sta $dc00               ; joystick 2 reads directly
        lda #0
        sta $dc02               ; DDR A = 0: tutti i bit in ingresso
```

Il joystick in porta 2 è collegato alla **porta A della CIA1** (`$DC00`), la
stessa linea che il KERNAL usa come uscita per scandire le colonne della
tastiera. Con `DDRA = 0` tutti i bit diventano ingressi: leggendo `$DC00` si
ottengono direttamente gli interruttori del joystick, senza interferenze dei
valori di uscita della scansione. Scrivere `$FF` nel registro dati è una
precauzione: se un giorno un bit tornasse in uscita, non tirerebbe la linea
a 0.

### 3.2 `init_hero` ([hero.asm:43-70](game/src/hero.asm#L43-L70))

```asm
        lda #<HERO_START_X       ; 148
        sta hero_x
        lda #>HERO_START_X       ; 0
        sta hero_x+1
        lda #HERO_START_Y        ; 111
        sta hero_y
        lda #DIR_DOWN
        sta hero_dir
        lda #0
        sta hero_moving
        sta walk_frame
        sta walk_timer
        sta joy_state
        sta $d017               ; nessuna espansione verticale
        sta $d01d               ; nessuna espansione orizzontale
        sta $d01b               ; priorità: sprite davanti al bitmap
        lda #9
        sta $d025               ; codice 01: marrone
        lda #10
        sta $d026               ; codice 11: pelle
        lda #5
        sta $d027               ; codice 10 dello sprite 0: verde
        lda #1
        sta $d01c               ; sprite 0 multicolor
        sta $d015               ; sprite 0 visibile
        jsr animate_hero        ; imposta il puntatore
        jmp place_hero          ; imposta $D000/$D001/$D010 (tail call)
```

- Il registro A già azzerato serve a pulire più variabili e registri di fila;
  lo stesso vale per il valore 1 (`$D01C` e `$D015` vogliono entrambi il
  bit 0).
- **(148, 111)** mette lo sprite al centro: 148 + 12 = 160, cioè metà dei 320
  pixel. I piedi cadono sulle celle (15-16, 19-20), che sono pavimento
  (sezione 6.8).
- Lo sprite diventa visibile qui, ma lo schermo è ancora spento (`$D011` bit 4
  = 0) e a display spento il VIC non mostra nemmeno gli sprite. Comparirà
  insieme alla stanza.

---

## 4. Il frame di gioco

```asm
main_loop:
        jsr wait_frame          ; riga raster 0
        inc frame_count ...
        jsr read_joystick
        jsr play_frame          ; update_hero → animate_hero → place_hero
        ... ogni 8 frame: animate_torches
        jmp main_loop
```

`play_frame` ([main.asm:95-99](game/src/main.asm#L95-L99)) è il punto in cui i
capitoli successivi aggiungeranno nemici, oggetti e combattimento. L'ordine dei
passi è importante:

1. **leggere** l'input;
2. **aggiornare** lo stato, con le collisioni;
3. **scegliere** il fotogramma;
4. **scrivere** i registri del VIC.

Scrivere i registri per ultimi garantisce che il VIC mostri sempre uno stato
coerente: posizione e fotogramma dello stesso frame.

---

## 5. `read_joystick` ([hero.asm:34-40](game/src/hero.asm#L34-L40))

```asm
read_joystick:
        lda $dc00               ; bit = 0 se premuto
        eor #$ff                ; inverte: 1 = premuto
        and #$1f                ; solo i 5 interruttori
        sta joy_state
joy_ready:                      ; the test injects input
        rts
```

| Bit | 0 | 1 | 2 | 3 | 4 |
|---|---|---|---|---|---|
| `$DC00` | su | giù | sinistra | destra | fuoco |
| costante | `JOY_UP` 1 | `JOY_DOWN` 2 | `JOY_LEFT` 4 | `JOY_RIGHT` 8 | `JOY_FIRE` 16 |

Gli interruttori sono **attivi bassi**: premuto = 0. `eor #$FF` li inverte,
così il resto del codice ragiona in logica positiva (`and #JOY_LEFT` / `bne` =
premuto). `and #$1F` scarta i bit 5-7, che non sono interruttori.

L'etichetta `joy_ready` non serve al programma: è il **punto d'aggancio dei
test automatici**. Il test può fermare l'emulatore lì e sovrascrivere
`joy_state` con un input scripted, prima che il gioco lo usi. Il bit del fuoco
viene letto ma in questo step non è usato.

---

## 6. Movimento e collisioni

### 6.1 `update_hero`: scelta della direzione ([hero.asm:74-101](game/src/hero.asm#L74-L101))

```asm
update_hero:
        lda #0
        sta hero_moving         ; per ora fermo
        sta hero_block          ; per ora niente ostacolo
        lda joy_state
        and #JOY_LEFT | JOY_RIGHT
        beq vertical            ; nessun input orizzontale
        and #JOY_LEFT           ; A contiene ancora i bit 2-3
        beq go_right
        lda #DIR_LEFT
        sta hero_dir
        jmp try_move
go_right:
        lda #DIR_RIGHT
        sta hero_dir
        jmp try_move
vertical:
        lda joy_state
        and #JOY_UP | JOY_DOWN
        beq update_done         ; leva al centro: nulla da fare
        and #JOY_UP
        beq go_down
        lda #DIR_UP
        sta hero_dir
        jmp try_move
go_down:
        lda #DIR_DOWN
        sta hero_dir            ; prosegue in try_move
```

- **Niente diagonali: l'orizzontale vince.** Con su+destra l'esploratore va a
  destra. Un solo asse per volta semplifica le collisioni (un solo bordo della
  hitbox da testare) e anche i fotogrammi (4 direzioni).
- **Doppio `and`.** Dopo `and #JOY_LEFT|JOY_RIGHT` in A restano solo i bit 2
  e 3. Il secondo `and #JOY_LEFT` non ha bisogno di rileggere `joy_state`. Se
  sono premute sia sinistra sia destra (impossibile con un joystick reale)
  vince la sinistra.
- **La direzione cambia anche se il passo è bloccato.** `hero_dir` si aggiorna
  prima del test di collisione: spingendo contro un muro l'esploratore si gira
  verso il muro e resta fermo, mostrando il fotogramma di riposo in quella
  direzione.

### 6.2 `try_move`: il ciclo dei passi ([hero.asm:102-115](game/src/hero.asm#L102-L115))

```asm
try_move:
        lda #HERO_SPEED         ; 1
        sta step_count
step_loop:
        jsr step_blocked        ; A = 0 libero, 1 muro, 2 porta
        sta hero_block
        bne update_done         ; solido: stop
        jsr step_forward        ; un pixel avanti
        lda #1
        sta hero_moving
        dec step_count
        bne step_loop
update_done:
        rts
```

Il movimento avviene **un pixel per volta, controllando prima di muoversi**.
Con `HERO_SPEED = 1` il ciclo gira una volta sola, ma è scritto per qualunque
velocità. Con velocità 2 o 3, ogni pixel viene testato separatamente:
l'esploratore si ferma **esattamente a contatto** del muro, senza mai entrarci
e senza bisogno di "tirarlo fuori" dopo.

**Un dettaglio sui flag.** `sta hero_block` non modifica i flag, quindi `bne`
usa il flag Z lasciato dall'ultima `lda` dentro `is_solid`
(`lda (cell_ptr),y` oppure `lda #1`). Tutta la catena
`step_blocked → is_solid` restituisce il risultato **sia in A sia in Z**: il
chiamante lo salva e lo testa senza un `cmp`.

`hero_block` resta a disposizione dei capitoli successivi: un 2 significa "ho
spinto contro una porta", e servirà per aprirla con la chiave.

### 6.3 La hitbox: solo i piedi

```
     colonna sprite:  0     6    11    17    23
riga  0 ┌──────────────────────────────┐
        │          testa / busto       │
     13 │      ┌───────────┐           │  BOX_TOP
        │      │  piedi    │           │
     18 │      └───────────┘           │  BOX_BOTTOM
     20 └──────────────────────────────┘
          BOX_LEFT=6  BOX_MID=11  BOX_RIGHT=17
```

La hitbox è un rettangolo di **12×6 pixel attorno ai piedi** (x 6-17,
y 13-18), non tutto lo sprite. È la convenzione della vista dall'alto "a tre
quarti": conta dove poggiano i piedi, e la testa può sovrapporsi alla parete
dietro. Con `$D01B = 0` lo sprite è sempre disegnato **davanti** al bitmap,
quindi avvicinandosi a un muro in alto la testa copre i mattoni, come ci si
aspetta.

### 6.4 `step_blocked`: quali punti testare ([hero.asm:121-172](game/src/hero.asm#L121-L172))

Si testano i punti **un pixel oltre** il bordo della hitbox nella direzione di
marcia:

| Direzione | Y del test | X del test | Punti |
|---|---|---|---|
| giù | `hero_y + 19` (`BOX_BOTTOM+1`) | +6, +11, +17 | 3 |
| su | `hero_y + 12` (`BOX_TOP−1`) | +6, +11, +17 | 3 |
| sinistra | +13, +18 | `hero_x + 5` (`BOX_LEFT−1`) | 2 |
| destra | +13, +18 | `hero_x + 18` (`BOX_RIGHT+1`) | 2 |

**Perché 3 punti in verticale e 2 in orizzontale.** Una cella è larga 8 pixel.
Un muro di una cella può "scivolare" fra due punti di test se questi distano 8
pixel o più.

- **Lato orizzontale della hitbox (12 pixel):** con i soli estremi 6 e 17
  (distanza 11) una cella può stare tutta in mezzo. Esempio:
  `hero_x + 6 = 7` (cella 0) e `hero_x + 17 = 18` (cella 2), mentre la cella 1
  (pixel 8-15) non verrebbe testata. Il punto centrale `BOX_MID = 11` riduce
  gli intervalli a 5 e 6 pixel, entrambi < 8: **ogni cella toccata dalla
  hitbox contiene almeno un punto di test**.
- **Lato verticale (6 pixel, 13-18):** la distanza è 5 < 8, quindi bastano i
  due estremi.

Codice del caso verticale:

```asm
blocked_down:
        lda hero_y
        clc
        adc #BOX_BOTTOM + 1      ; 19: costante calcolata dall'assembler
        sta probe_y
        jmp blocked_row
blocked_up:
        lda hero_y
        clc
        adc #BOX_TOP - 1         ; 12
        sta probe_y
blocked_row:
        lda #BOX_LEFT
        jsr probe_column        ; probe_x = hero_x + 6
        jsr is_solid
        bne blocked_done        ; il primo solido basta
        lda #BOX_MID
        jsr probe_column
        jsr is_solid
        bne blocked_done
        lda #BOX_RIGHT
        jsr probe_column
        jmp is_solid            ; tail call: il suo rts torna al chiamante
blocked_done:
        rts
```

- **Uscita anticipata.** Il primo punto solido basta e il suo valore (1 o 2) è
  quello restituito: per questo la routine dice "il valore della *prima* cella
  solida trovata".
- **Tail call.** L'ultimo test è un `jmp is_solid`: il risultato di
  `is_solid` diventa direttamente quello di `step_blocked`.
- **Smistamento della direzione.** Il caso giù non ha un `cmp`: è quello che
  resta quando gli altri tre test falliscono, e il codice ci arriva "cadendo"
  dopo i `beq`.

Il caso orizzontale è simmetrico: si fissa `probe_x` con `probe_column` e si
variano le Y (`blocked_column`).

### 6.5 `probe_column` ([hero.asm:175-182](game/src/hero.asm#L175-L182))

```asm
probe_column:                   ; probe_x = hero_x + A
        clc
        adc hero_x
        sta probe_x
        lda hero_x+1
        adc #0
        sta probe_x+1
        rts
```

È una somma a 16 bit di un offset a 8 bit: X può superare 255, quindi serve
anche il byte alto.

### 6.6 `is_solid`: da pixel a cella ([hero.asm:214-246](game/src/hero.asm#L214-L246))

**a) Fuori dallo schermo = solido.**

```asm
        lda probe_x+1
        beq solid_x_ok          ; X < 256
        cmp #1
        bne solid_outside       ; byte alto ≥ 2 (o $FF): fuori
        lda probe_x
        cmp #64                 ; X = 256 + basso; ≥ 320 se basso ≥ 64
        bcs solid_outside
solid_x_ok:
        lda probe_y
        cmp #200
        bcs solid_outside       ; Y ≥ 200: fuori
```

320 = `$0140`: con byte alto 1 il limite è il byte basso `$40` = 64. Un X
**negativo**, cioè `hero_x` sceso sotto 0 per un `dec` a 16 bit, diventa
`$FFxx`: il byte alto `$FF` cade nel caso "≠ 0 e ≠ 1" ed è trattato come
fuori. Un solo controllo copre così sia il bordo destro sia l'underflow a
sinistra.

**b) Riga: tabella degli indirizzi.**

```asm
        lsr a
        lsr a
        lsr a                   ; riga = Y / 8 (0-24)
        asl a                   ; ×2: la tabella è di parole
        tax
        lda row_offsets,x
        sta cell_ptr
        lda row_offsets+1,x
        sta cell_ptr+1
...
row_offsets:
        .word SOLID_MAP + range(25) * 40
```

Le tabelle delle righe di `text.asm` erano due array separati (`_lo`/`_hi`).
Qui c'è un solo array di parole little-endian, quindi l'indice va raddoppiato:
`lsr ×3` seguito da `asl` dà `(Y/8)*2`. Non si può scrivere `lsr ×2` +
`and #$FE`, perché va scartato il bit 2 di Y, non tenuto: `lsr ×3` + `asl`
azzera correttamente il bit 0 dell'indice.

**c) Colonna: X a 9 bit diviso 8.**

```asm
        lda probe_x+1           ; 0 oppure 1
        lsr a                   ; bit 8 di X → Carry
        lda probe_x
        ror a                   ; Carry entra nel bit 7: A = X / 2 (8 bit)
        lsr a
        lsr a                   ; A = X / 8 (0-39)
        tay
        lda (cell_ptr),y        ; valore di SOLID_MAP: 0, 1 o 2
        rts
```

È il passaggio più elegante della routine. X ha 9 bit significativi (0-319) e
non sta in un registro. Il trucco:

1. `lsr` del byte alto (0 o 1) mette il **bit 8** nel carry;
2. `ror` del byte basso fa entrare quel bit nel bit 7 e fa uscire il bit 0. A
   ora contiene `X >> 1`, che sta in 8 bit (max 159);
3. altri due `lsr` danno `X >> 3`.

Esempio: X = 300 = `$012C`. `lsr` di `$01` → C = 1; `ror` di `$2C`
(`0010 1100`) → `1001 0110` = `$96` = 150; `lsr lsr` → 37. Infatti
300 / 8 = 37,5 → 37 ✓.

**d) Il risultato è già il valore cercato.** `SOLID_MAP` contiene 0
(pavimento), 1 (muro) o 2 (porta), scritti da `draw_half` nello step 01.
`is_solid` restituisce quel byte senza interpretarlo: il significato resta
tutto nei dati.

### 6.7 `step_forward` ([hero.asm:184-209](game/src/hero.asm#L184-L209))

```asm
        inc hero_y              ; giù (caso di default)
        ...
forward_up:     dec hero_y
forward_left:
        lda hero_x
        bne left_low            ; se il byte basso non è 0 non c'è prestito
        dec hero_x+1
left_low:
        dec hero_x
forward_right:
        inc hero_x
        bne forward_done
        inc hero_x+1
```

Sono i due idiomi a 16 bit del 6502:

- **incremento:** `inc` del byte basso, e se diventa 0 `inc` dell'alto;
- **decremento:** si controlla il byte basso **prima** del `dec`, perché il
  prestito nasce quando si passa da `$00` a `$FF`, e dopo il `dec` il flag Z
  non lo segnala.

### 6.8 Verifica sulla Moss Gate

`SOLID_MAP` ricostruita dalla mappa e dagli attributi del `.prg` (`.`
pavimento, `#` muro, `D` porta/cancello):

```
    0         1         2         3
    0123456789012345678901234567890123456789
 3  ##################DDDD##################
 ...
 6  ##################DDDD##################
 7  ####..............DDDD..............####
 8  ####................................####
11  ######............................######   ← torce T/t
13  ####..##........................##..####   ← pilastri P
15  ####..##........................##..####   ← piedi alla partenza (col 19-20)
17  ######............................######
20  ####................................####
21  ##################....##################   ← apertura E
22  ##################....##################
23  ########################################   ← fuori mappa: solido da clear_screen
```

Partendo da (148, 111) e tenendo premuta una direzione, la simulazione della
logica di `hero.asm` dà:

| Direzione | Si ferma a | Pixel percorsi | `hero_block` | Motivo |
|---|---|---|---|---|
| sinistra | (58, 111) | 90 | 1 | `58 + 5 = 63` → colonna 7, il pilastro |
| destra | (238, 111) | 90 | 1 | `238 + 18 = 256` → colonna 32, il pilastro |
| su | (148, 51) | 60 | **2** | `51 + 12 = 63` → riga 7, il cancello |
| giù | (148, 165) | 54 | 1 | `165 + 19 = 184` → riga 23, fuori mappa |

Due osservazioni:

- Verso l'alto si incontra il **cancello**, e `hero_block` vale 2: è
  l'informazione che lo step successivo userà per il portale.
- Verso il basso l'esploratore entra nell'apertura `E` (righe 21-22 libere) ma
  si ferma sulla riga 23, che `clear_screen` ha riempito di 1. È quanto dice
  il README: *"the map simply ends"*.

---

## 7. `animate_hero` ([hero.asm:249-273](game/src/hero.asm#L249-L273))

```asm
animate_hero:
        lda hero_moving
        bne walking
        lda #0                  ; fermo: fotogramma di riposo
        sta walk_frame
        sta walk_timer
        beq set_pointer         ; A = 0: salto sempre preso
walking:
        inc walk_timer
        lda walk_timer
        cmp #WALK_RATE          ; 8
        bne set_pointer
        lda #0
        sta walk_timer
        lda walk_frame
        eor #1                  ; 0 ↔ 1
        sta walk_frame
set_pointer:
        lda hero_dir
        asl a                   ; dir × 2
        ora walk_frame          ; + 0/1 (il bit 0 è libero dopo asl)
        clc
        adc #HERO_POINTER       ; + 0
        sta SPRITE_PTRS         ; $47F8: puntatore dello sprite 0
        rts
```

- **`beq set_pointer` come salto incondizionato.** Dopo `lda #0` il flag Z è
  sicuramente 1, quindi il salto è sempre preso: 2 byte invece dei 3 di un
  `jmp`. È lo stesso idioma di `bne` dopo `inc text_pos` nel testo.
- **Ritmo.** Ogni 8 frame di cammino si alterna il fotogramma: 160 ms per
  passo, un ciclo completo di 320 ms. È lo stesso `WALK_RATE` di 8 usato per
  le torce.
- **Il fermo azzera tutto.** Appena il movimento si interrompe torna il
  fotogramma 0 della direzione, e il timer riparte da 0. Una conseguenza: i
  primi 8 frame di ogni camminata mostrano il fotogramma 0 (che è anche quello
  di riposo), e solo dopo compare il passo B.
- **`ora` invece di `adc`.** Dopo `asl` il bit 0 è sempre 0: è lo stesso
  trucco di `ora #16` in `draw_half`.
- **`adc #HERO_POINTER`** vale 0 e non cambia nulla. Rende il codice corretto
  anche se i fotogrammi venissero spostati: basterebbe cambiare `SPRITE_DATA`.

Il puntatore si cambia scrivendo **un solo byte** a `$47F8`: il VIC legge i
dati dello sprite dal nuovo indirizzo a partire dal frame successivo. Non si
copiano i 64 byte del fotogramma, a differenza delle fiamme delle torce, che
stanno nel bitmap e devono essere copiate.

---

## 8. `place_hero`: coordinate del VIC ([hero.asm:276-295](game/src/hero.asm#L276-L295))

```asm
place_hero:
        lda $d010
        and #%11111110          ; 9° bit X dello sprite 0 spento
        sta $d010               ; gli altri sprite non cambiano
        lda hero_x
        clc
        adc #24                 ; VIC X = schermo X + 24
        sta $d000
        lda hero_x+1
        adc #0                  ; riporto della somma
        beq x_below_256
        lda $d010
        ora #1                  ; 9° bit acceso
        sta $d010
x_below_256:
        lda hero_y
        clc
        adc #50                 ; VIC Y = schermo Y + 50
        sta $d001
        rts
```

**Gli offset 24 e 50.** Nel sistema del VIC lo sprite con X = 24 e Y = 50 ha
l'angolo superiore sinistro sul primo pixel dell'area di 320×200 (40 colonne,
25 righe). Tenere `hero_x`/`hero_y` in coordinate dello schermo e aggiungere
l'offset solo qui fa sì che collisioni, `SOLID_MAP` e bitmap usino tutti lo
stesso sistema.

**Il 9° bit.** La X del VIC va da 0 a 511 ma `$D000` ha 8 bit: il bit 8 di ogni
sprite sta in `$D010`, un bit per sprite. Lo schermo arriva a 319 + 24 = 343,
quindi serve. Il codice:

1. spegne **solo** il bit 0, con `and` a maschera, lasciando quelli degli altri
   sprite che arriveranno nei prossimi capitoli: è il senso di *"place_hero
   sets only the ninth X bit of its own sprite"*;
2. somma 24 a 16 bit. L'`adc #0` sul byte alto raccoglie anche il riporto
   della somma, quindi un `hero_x` di 240 (byte alto 0) diventa 264 e accende
   correttamente il 9° bit;
3. riaccende il bit 0 se il risultato è ≥ 256.

Esempio alla partenza: X = 148 + 24 = 172 (`$AC`), 9° bit spento;
Y = 111 + 50 = **161**. A destra contro il pilastro: X = 238 + 24 = 262 =
`$106`, quindi `$D000 = $06` e il bit 0 di `$D010` è acceso.

`$D010` viene scritto due volte (spento, poi eventualmente acceso). Se il
raster fosse sullo sprite, potrebbe vedersi un pixel sbagliato per un istante.
Non succede perché `place_hero` gira subito dopo `wait_frame`, nel bordo
superiore, come le torce.

---

## 9. Il collegamento con `enter_room` e i tempi

[world.asm](game/src/world.asm) aggiunge una sola riga:

```asm
room_drawn:
        jsr animate_torches
        jsr place_hero          ; ← nuovo: registri dello sprite pronti
        jsr wait_frame
        lda #$3b                ; display on
        sta $d011
```

Quando lo schermo si riaccende, stanza, fiamme e sprite compaiono insieme e
coerenti fin dal primo frame.

**Costo per frame**, stimato contando le istruzioni:

| Routine | Cicli circa |
|---|---|
| `read_joystick` | ~20 |
| `update_hero` con un passo verticale (3 test) | ~300 |
| `update_hero` con un passo orizzontale (2 test) | ~220 |
| `animate_hero` | ~40 |
| `place_hero` | ~50 |
| **Totale** | **~400**, circa 7 righe raster |

Anche sommando le torce (~600-900 cicli ogni 8 frame), tutto finisce verso la
riga raster 20-25, ben prima della riga 51 dove inizia l'area visibile. Lo
sprite viene quindi sempre aggiornato fuori dallo schermo visibile.

---

## 10. Osservazioni e limiti di questo step

- **Un solo sprite.** Sono configurati solo i bit 0 di `$D015`, `$D01C` e
  `$D010`. Il codice però è già scritto per non toccare gli altri bit (`$D010`
  mascherato) in vista di nemici e oggetti.
- **Priorità fissa davanti al bitmap.** L'esploratore non può passare "dietro"
  un elemento della scena; con la hitbox ai piedi l'effetto è comunque
  credibile.
- **Velocità intera, 1 pixel per frame (50 pixel/s).** Non ci sono velocità
  frazionarie: rallentare significherebbe muoversi 1 frame su 2.
- **Il fuoco è letto ma non usato.** Servirà per la spada nello step del
  combattimento (in `sprites.py` ci sono già i fotogrammi `BLADE_*`).
- **La collisione non distingue lo scivolamento.** Se un piede tocca uno
  spigolo, l'esploratore si ferma del tutto invece di scivolare lungo il muro,
  perché la direzione è una sola.
- **L'apertura `E` non porta ancora da nessuna parte**: arrivano la riga 23
  solida e `hero_block = 1`. Il cambio di stanza arriva nello step 03.
