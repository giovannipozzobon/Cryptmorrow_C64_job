# Cryptmorrow 03 – Il dungeon: 16 stanze, uscite, cambio di stanza e HUD

Analisi del codice di `chain/03-dungeon`, limitata a ciò che è nuovo rispetto
allo step 02. Le parti precedenti sono descritte in:

- [../01-first-room/TILE_ENGINE.md](../01-first-room/TILE_ENGINE.md): motore a
  tile, testo, torce;
- [../02-explorer/SPRITES.md](../02-explorer/SPRITES.md): sprite, joystick,
  collisioni.

Gli esempi numerici sono valori reali, letti dal `cryptmorrow.prg` di questo
step, dai test (`tests/verify_game.py`) e dalle misure salvate in
`variants/03-dungeon/*/evidence`.

---

## 0. Cosa cambia rispetto allo step 02

| File | Modifica |
|---|---|
| [hud.asm](game/src/hud.asm) | **nuovo**: `print_hud`, `hud_update`, `print_score`, `print_digit` e i testi fissi dell'HUD |
| [world.asm](game/src/world.asm) | costanti dei bordi, `check_exits`, le quattro uscite, `change_room`; `init_game` inizializza energia, chiavi, sigilli e punteggio; nuove variabili di stato |
| [text.asm](game/src/text.asm) | costanti dei colori, `print_list`, `print_at` e la codifica `.enc "glyphs"` per scrivere stringhe nel sorgente |
| [main.asm](game/src/main.asm) | chiama `print_hud` all'avvio e `check_exits` in `play_frame`; include `hud.asm` |
| `hero.asm`, `room.asm`, `memory.asm`, `data.asm` | identici |
| asset | identici: le 16 stanze erano già in `rooms.bin` fin dallo step 01, ma finora se ne disegnava solo una |

Il codice ora va da `$0801` a `$0F97` (`code_end`), sempre molto sotto
`SPRITE_DATA` (`$4000`).

---

## 1. La mappa del dungeon

### 1.1 Griglia e numerazione

Il dungeon è una griglia 4×4 descritta in `assets/rooms/dungeon.txt`. Ogni
stanza ha un numero (`room_slot`) = riga × 4 + colonna, e occupa la pagina
`ROOM_DATA + room_slot × 256` (vedi `room_address` nello step 01).

Dal `.prg` (zona: 0 atrio, 1 A, 2 B, 3 C):

```
          col 0               col 1               col 2                col 3
riga 0   0 BONE PIT (0)       1 MOSS GATE (0)      2 OLD WELL (0)       3 BLACK CISTERN (B)
               │               ║portale  │              │                     │
riga 1   4 ROOT CELLAR (0) ── 5 CROSSROADS (0) ── 6 LONG GALLERY (0) ═D═ 7 FLOODED STAIR (B)
               D                    │                                         │
riga 2   8 OSSUARY (A)        9 SUNKEN HALL (0) ═D═ 10 AMBER HALL (C)     11 DROWNED SHRINE (B)
               │                                        │
riga 3  12 CATACOMBS (A) ──  13 BONE SHRINE (A)   14 TREASURY (C) ──  15 SUN VAULT (C)
```

`──` / `│` = apertura `E` (passaggio libero); `D` = porta chiusa (cella di
valore 2 in `SOLID_MAP`); `║portale` = il cancello `G` della Moss Gate. Fra
Bone Pit e Moss Gate non c'è collegamento.

Le aperture lette dal `.prg`, con le colonne o righe di metatile su ciascun
bordo:

| Stanza | Aperture |
|---|---|
| 0 Bone Pit | S 10-11 |
| 1 Moss Gate | N 9-10 (cancello del portale), S 9-10 |
| 2 Old Well | S 16-17 |
| 3 Black Cistern | S 9-10 |
| 4 Root Cellar | N 10-11, E 4-5, S 9-10 (**porta**) |
| 5 Crossroads | N 9-10, W 4-5, E 4-5, S 9-10 |
| 6 Long Gallery | N 16-17, W 4-5, E 4-5 (**porta**) |
| 7 Flooded Stair | N 9-10, W 4-5, S 9-10 |
| 8 Ossuary | N 9-10, S 4-5 |
| 9 Sunken Hall | N 9-10, E 5-6 (**porta**) |
| 10 Amber Hall | W 5-6, S 9-10 |
| 11 Drowned Shrine | N 9-10 |
| 12 Catacombs | N 4-5, E 6-7 |
| 13 Bone Shrine | W 6-7 |
| 14 Treasury | N 9-10, E 6-7 |
| 15 Sun Vault | W 6-7 |

Ogni apertura ha la sua gemella **nella stessa posizione** sul bordo opposto
della stanza vicina. Esempio: Moss Gate S 9-10 ↔ Crossroads N 9-10; Root
Cellar N 10-11 ↔ Bone Pit S 10-11.

### 1.2 Cosa si può visitare in questo step

Le porte (`D`) e il portale sono ancora chiusi: sono celle solide con
valore 2. Partendo dalla Moss Gate si raggiungono solo **7 stanze**:
1 → 5 → 4, 6, 9; 4 → 0; 6 → 2. **Sono tutte dell'atrio (zona 0).**

`set_zone` quindi copia la palette una sola volta, all'ingresso nella prima
stanza (`colour_zone` parte da `$FF`). Nei cambi di stanza successivi trova
sempre la stessa zona ed esce subito (`beq zone_ready`). Le zone A, B e C
esistono nei dati ma diventano raggiungibili solo con le chiavi, nello
step 04.

### 1.3 Le garanzie del builder (`assets/dungeon.py`)

Il codice 6502 dei cambi di stanza **non fa nessun controllo**: niente limiti
della griglia, niente verifica che la stanza vicina esista o abbia
un'apertura corrispondente. Questi controlli li fa il builder, che rifiuta il
dungeon se:

- un'apertura `E`/`D` non sta **su un solo bordo**, cioè è all'interno o in un
  angolo (`openings`);
- un simbolo diverso da muro, `G`, `E` o `D` sta sul bordo, cioè "lascia il
  bordo aperto";
- dietro un'apertura non c'è pavimento (`WALKABLE_INSIDE`);
- un'apertura porta fuori dalla griglia o in un posto vuoto (`check_links`:
  *"leads to no room"*), oppure la stanza vicina non ha **le stesse
  posizioni** sul bordo opposto (*"does not match"*);
- il gioco non si può completare (`solve`), ma questo riguarda gli step
  successivi.

Per le aperture est e ovest `check_links` controlla anche
`there // GRID == slot // GRID`: il vicino deve stare sulla stessa riga. Senza
questo, un'uscita est dalla colonna 3 porterebbe alla colonna 0 della riga
successiva (slot + 1).

Queste regole sono ciò che rende corretta l'aritmetica del codice:
`room_slot ± 1` o `± 4` porta sempre a una stanza valida, e conservare l'altra
coordinata (X uscendo in verticale, Y in orizzontale) fa comparire
l'esploratore **dentro l'apertura gemella**.

---

## 2. La geometria delle uscite

### 2.1 L'idea: l'anello esterno

L'area della mappa va dalla riga di celle 3 alla 22 e dalla colonna 0 alla 39.
L'**anello più esterno** (riga 3, riga 22, colonna 0, colonna 39) è riempito
di muri, **tranne nelle aperture**. Il commento di `world.asm` lo dice
esplicitamente:

```
; A room is left when the hitbox enters the outermost
; ring of cells of the playfield. Walls fill that ring
; except in the openings, so only there can it happen.
```

Il test di uscita, quindi, non deve sapere dove sono le aperture: controlla
solo **se la hitbox è entrata nell'anello**. Le collisioni dello step 02
garantiscono già che possa entrarci soltanto attraverso un'apertura.

### 2.2 Le costanti, derivate dalla hitbox

```asm
NORTH_EDGE = FIRST_ROW * 8 + 7 - BOX_TOP                  ; 3*8+7-13       = 18
SOUTH_EDGE = (FIRST_ROW + CELL_ROWS - 1) * 8 - BOX_BOTTOM ; (3+20-1)*8-18  = 158
WEST_EDGE  = 7 - BOX_LEFT                                 ; 7-6            = 1
EAST_EDGE  = 39 * 8 - BOX_RIGHT                           ; 312-17         = 295
```

I valori nel file `.lbl` coincidono: `NORTH_EDGE = $12`, `SOUTH_EDGE = $9E`,
`WEST_EDGE = $01`, `EAST_EDGE = $127`.

| Uscita | Condizione su sprite | Equivale a | Cella dell'anello |
|---|---|---|---|
| nord | `hero_y ≤ 18` | bordo alto hitbox `hero_y + 13 ≤ 31` | riga 3 = pixel 24-**31** |
| sud | `hero_y ≥ 158` | bordo basso `hero_y + 18 ≥ 176` | riga 22 = pixel **176**-183 |
| ovest | `hero_x ≤ 1` | bordo sinistro `hero_x + 6 ≤ 7` | colonna 0 = pixel 0-**7** |
| est | `hero_x ≥ 295` | bordo destro `hero_x + 17 ≥ 312` | colonna 39 = pixel **312**-319 |

La condizione scatta appena **un pixel** della hitbox entra nella cella
dell'anello. Le costanti sono scritte come formule, così cambiando la hitbox
(`BOX_*`) o la posizione della mappa (`FIRST_ROW`) i bordi si aggiornano da
soli.

### 2.3 Perché i bordi sono davvero raggiungibili

Con la logica di collisione dello step 02, fin dove arriva l'esploratore
dentro un'apertura prima che `check_exits` intervenga:

| Direzione | L'uscita scatta a | La collisione lo fermerebbe a | Perché |
|---|---|---|---|
| sud | Y = 158 | Y = 165 | `165 + 19 = 184`: riga 23, fuori mappa, solida |
| nord | Y = 18 | Y = 11 | `11 + 12 = 23`: riga 2, solida |
| ovest | X = 1 | – (vedi 2.4) | la colonna 0 dell'apertura è pavimento |
| est | X = 295 | X = 302 | `302 + 18 = 320`: fuori schermo, `is_solid` = 1 |

In tutti i casi il bordo dell'uscita viene raggiunto **prima** del punto in cui
la collisione ferma l'esploratore. Lo step 02 si fermava a Y = 165 nella Moss
Gate; ora a Y = 158 si passa alla stanza sotto.

### 2.4 I due `.cerror`

```asm
        .cerror EAST_EDGE < 256, "check_exits: X high byte"
        .cerror HERO_SPEED > WEST_EDGE + 1, "X could wrap"
```

**Il primo** protegge un'ottimizzazione di `check_exits`: il codice assume che
l'uscita est sia **sempre** nella metà destra (X ≥ 256, byte alto = 1) e
quella ovest **sempre** nella metà sinistra (byte alto = 0). Così basta
guardare il byte alto per sapere quale dei due bordi testare, e poi
confrontare un solo byte. Se una hitbox diversa portasse `EAST_EDGE` sotto
256, il test non funzionerebbe più e la build si fermerebbe.

**Il secondo** riguarda l'underflow a sinistra:

- la colonna 0 di un'apertura ovest è pavimento, e `is_solid` testa
  `hero_x + 5`;
- se `hero_x` scendesse sotto 0 diventerebbe `$FFFF`, e `$FFFF + 5` = `$0004`
  (la somma a 16 bit "gira"): sarebbe ancora la colonna 0, cioè pavimento, e
  la collisione non fermerebbe l'esploratore;
- a quel punto `check_exits` vedrebbe il byte alto ≠ 0, confronterebbe il byte
  basso `$FF` con il bordo est e **uscirebbe a est** invece che a ovest.

Il problema si evita se `check_exits` scatta **prima** che X possa diventare
negativo. Con l'uscita a X ≤ 1, in un frame l'esploratore passa da X ≥ 2 a
X ≥ 2 − `HERO_SPEED`. Serve `HERO_SPEED ≤ 2 = WEST_EDGE + 1`, ed è esattamente
quello che controlla il `.cerror`.

---

## 3. `check_exits`, istruzione per istruzione ([world.asm:42-59](game/src/world.asm#L42-L59))

È chiamata in `play_frame` subito dopo `update_hero`, quando la posizione del
frame è già definitiva:

```asm
play_frame:
        jsr update_hero
        jsr check_exits         ; may draw another room
        jsr animate_hero
        jsr place_hero
        rts
```

### 3.1 Bordi verticali

```asm
check_exits:
        lda hero_y
        cmp #NORTH_EDGE + 1     ; confronta con 19
        bcc exit_north          ; C=0 ⇔ Y < 19 ⇔ Y ≤ 18
        cmp #SOUTH_EDGE         ; confronta con 158
        bcs exit_south          ; C=1 ⇔ Y ≥ 158
```

Dopo `cmp` il carry vale 1 se A ≥ operando (senza segno) e 0 se A < operando.
Il 6502 ha solo "minore" (`bcc`) e "maggiore o uguale" (`bcs`). Per esprimere
"Y ≤ 18" il codice confronta con **18 + 1** e usa `bcc`. Il secondo `cmp`
riusa A, che contiene ancora `hero_y`: `cmp` non modifica il registro.

### 3.2 Bordi orizzontali

```asm
        lda hero_x+1
        bne east_half           ; X ≥ 256: solo l'est è possibile
        lda hero_x
        cmp #WEST_EDGE + 1      ; 2
        bcc exit_west           ; X ≤ 1
        rts                     ; nessuna uscita
east_half:
        lda hero_x
        cmp #<EAST_EDGE         ; byte basso di 295 = 39 ($27)
        bcs exit_east           ; 256 + basso ≥ 295 ⇔ basso ≥ 39
        rts
```

Grazie al primo `.cerror`, il confronto a 16 bit si riduce a **un test sul
byte alto + un confronto a 8 bit**. Nella metà destra X = 256 + byte basso,
quindi `X ≥ 295` ⇔ `basso ≥ 39`.

I bordi verticali sono testati per primi. In pratica non c'è conflitto, perché
il builder vieta le aperture negli angoli: la hitbox non può trovarsi in due
anelli contemporaneamente.

Costo: 15-25 cicli per frame quando non si esce.

---

## 4. Le quattro uscite ([world.asm:61-84](game/src/world.asm#L61-L84))

```asm
exit_north:
north_room:
        lda #SOUTH_EDGE - ENTRY_MARGIN      ; 158 - 8 = 150
        sta hero_y
        lda #<-GRID_WIDTH                   ; -4 = $FC
        jmp change_room
exit_south:
        lda #NORTH_EDGE + ENTRY_MARGIN      ; 18 + 8 = 26
        sta hero_y
        lda #GRID_WIDTH                     ; +4
        jmp change_room
exit_west:
        lda #<(EAST_EDGE - ENTRY_MARGIN)    ; 287 = $011F → $1F
        sta hero_x
        lda #>(EAST_EDGE - ENTRY_MARGIN)    ; $01
        sta hero_x+1
        lda #<-1                            ; $FF
        jmp change_room
exit_east:
        lda #WEST_EDGE + ENTRY_MARGIN       ; 1 + 8 = 9
        sta hero_x
        lda #0
        sta hero_x+1                        ; X < 256: byte alto a 0
        lda #1                              ; prosegue in change_room
```

### 4.1 Dove ricompare l'esploratore

| Uscita | Nuova coordinata | Hitbox nella nuova stanza | Coordinata conservata |
|---|---|---|---|
| nord | `hero_y = 150` | piedi 163-168, righe 20-21 | `hero_x` |
| sud | `hero_y = 26` | piedi 39-44, righe 4-5 | `hero_x` |
| ovest | `hero_x = 287` | piedi 293-304, colonne 36-38 | `hero_y` |
| est | `hero_x = 9` | piedi 15-26, colonne 1-3 | `hero_y` |

L'esploratore compare sul **bordo opposto**, cioè dalla parte dell'apertura
gemella. L'altra coordinata non cambia: è il motivo per cui il builder
pretende che le aperture gemelle siano nelle **stesse posizioni**.

### 4.2 `ENTRY_MARGIN`: l'isteresi

La nuova posizione è **8 pixel più all'interno** del bordo di uscita della
nuova stanza. Senza margine, ad esempio uscendo a nord e ricomparendo a
`hero_y = SOUTH_EDGE`, al frame successivo `check_exits` vedrebbe subito
`Y ≥ SOUTH_EDGE` e rimanderebbe l'esploratore indietro: un **ping-pong
infinito** fra due stanze. Con 8 pixel di margine, per tornare indietro bisogna
camminare deliberatamente 8 pixel verso il bordo, cioè 8 frame a 1 pixel per
frame. È la stessa idea dell'isteresi di un termostato.

### 4.3 Il passo nella griglia

| Uscita | Passo | Valore in A |
|---|---|---|
| nord | −4 | `<-GRID_WIDTH` = `$FC` |
| sud | +4 | `$04` |
| ovest | −1 | `<-1` = `$FF` |
| est | +1 | `$01` |

I passi negativi sono in complemento a due: `$FC` + 5 = `$101`, e il riporto
si perde, lasciando `$01`. Così `adc` fa da sottrazione e `change_room` ha
**un'unica somma** per tutte e quattro le direzioni. L'operatore `<` di 64tass
prende il byte basso di −4, che altrimenti non starebbe in un byte.

### 4.4 Due dettagli di forma

- **`north_room:`** è una seconda etichetta sullo stesso indirizzo di
  `exit_north`. Non serve al codice: è un punto d'aggancio per i test e gli
  strumenti, come `joy_ready` nello step 02.
- **Catena di fall-through.** `exit_east` non ha il `jmp`: cade direttamente in
  `change_room`, che a sua volta cade in `enter_room`. Anche `change_room` non
  ha un `rts` proprio: termina con l'`rts` di `enter_room`.

### 4.5 La variante didattica 03x: il byte alto dimenticato

[variants/03-dungeon/03x-high-byte](../../variants/03-dungeon/03x-high-byte)
toglie di proposito le due righe

```asm
        lda #0
        sta hero_x+1
```

da `exit_east`. L'esploratore esce con X ≥ 295, quindi il byte alto vale 1; il
nuovo byte basso è 9, e la posizione diventa X = 256 + 9 = **265**. Compare
vicino al muro **est** della nuova stanza invece che a ovest, e continua a
camminare verso l'uscita successiva. È il classico errore delle coordinate a
16 bit su un 6502: aggiornare un byte e dimenticare l'altro.

---

## 5. `change_room` ed `enter_room` ([world.asm:88-109](game/src/world.asm#L88-L109))

```asm
change_room:
        clc
        adc room_slot           ; A = passo nella griglia
        sta room_slot
enter_room:
        lda #$0b                ; display off
        sta $d011
room_blank:
        jsr room_address        ; room_ptr = page_ptr = $A000 + slot*256
        jsr set_zone            ; copia 1 KB solo se cambia zona
        jsr draw_room           ; 20 righe di celle + nome
room_drawn:
        jsr animate_torches     ; fiamme alla fase corrente
        jsr place_hero          ; sprite nella posizione d'ingresso
        jsr wait_frame          ; riga raster 0
        lda #$3b                ; display on
        sta $d011
room_shown:
        rts
```

### 5.1 Sequenza temporale di un cambio di stanza

1. **Frame N**, subito dopo `wait_frame`: `update_hero` sposta l'esploratore
   oltre il bordo, `check_exits` se ne accorge, aggiorna la coordinata e
   `room_slot`, poi entra in `enter_room`.
2. `$D011 = $0B`: bit 4 = 0, **schermo spento**. Il VIC mostra solo il colore
   del bordo (nero) e smette di leggere bitmap, screen RAM e sprite. Non ci
   sono nemmeno le badline, quindi la CPU ha tutti i cicli.
3. `room_address`, `set_zone`, `draw_room`: il disegno vero e proprio.
4. Torce e sprite vengono preparati mentre lo schermo è ancora spento.
5. `wait_frame` aspetta l'inizio di un frame, poi `$D011 = $3B` riaccende lo
   schermo **dalla riga 0**: il primo frame visibile è già completo.
6. `rts` torna in `play_frame`, che esegue `animate_hero` e `place_hero` e
   chiude il frame.

### 5.2 Quanto dura: le misure dei test

`tests/verify_game.py` misura proprio questo intervallo (funzione
`change_of_room`). Mette dei punti di arresto su `room_blank`,
`next_cell_row`, `room_drawn` e `room_shown`, e controlla tre cose:

- che lo schermo sia spento già a `room_blank`;
- che `draw_room` passi per `next_cell_row` **esattamente 20 volte**;
- che lo schermo non si riaccenda prima di `room_shown`.

Misura anche i cicli fra `room_blank` e `room_drawn`.

Nelle evidenze della variante
[03a-autumn-moss](../../variants/03-dungeon/03a-autumn-moss/evidence/step-test.json),
che ha lo stesso codice di questo step con colori diversi, i valori vanno da
**183.068 a 184.381 cicli**, a seconda della stanza. A 19.656 cicli per frame
PAL sono **circa 9,3 frame**: lo schermo resta nero per circa un decimo di
secondo più il frame d'attesa. È il classico effetto "flip-screen".

Questa misura è circa il 5% più alta della stima fatta contando le istruzioni
in `TILE_ENGINE.md` (~175.000 cicli).

### 5.3 Effetti collaterali

- Durante il disegno `main_loop` è fermo, quindi `frame_count` non avanza e la
  fase delle torce resta quella di prima. `animate_torches` la applica subito
  alle torce della nuova stanza.
- `hero_dir`, `walk_frame` e `walk_timer` non vengono toccati: se il joystick
  resta premuto, l'esploratore continua a camminare nella nuova stanza con la
  stessa animazione.
- `torch_count` viene azzerato da `draw_room`, quindi le torce della stanza
  precedente non vengono più animate.

---

## 6. Esempio completo: dalla Moss Gate alla Crossroads e ritorno

Si parte dalla posizione iniziale (148, 111) e si tiene premuto **giù**:

| Frame | `hero_y` | Cosa succede |
|---|---|---|
| 0 | 111 | partenza; piedi alle righe 15-16 |
| 1-46 | 112 … 157 | cammina nella stanza e nell'apertura sud (colonne di metatile 9-10 = celle 18-21; i piedi sono alle colonne 19-20) |
| 47 | **158** | `update_hero` arriva a 158 → `check_exits`: `158 ≥ SOUTH_EDGE` → `exit_south` |
| | 26 | `hero_y = 26`, `room_slot = 1 + 4 = 5` → `enter_room` disegna **THE CROSSROADS** (~9,3 frame neri) |
| poi | 27, 28 … | entra nella Crossroads dall'apertura nord (colonne 9-10, la gemella), con X ancora 148 |

Per tornare indietro si preme **su**: da Y = 26 servono 8 passi per arrivare a
Y = 18 (`≤ NORTH_EDGE`). Scatta `exit_north`, che imposta `hero_y = 150` e
`room_slot = 5 + $FC = 1`, e l'esploratore ricompare nella Moss Gate appena
sopra l'apertura sud.

---

## 7. L'HUD

### 7.1 Disposizione sullo schermo

```
riga  0  (vuota)
riga  1   ENERGY ********  +0  @0/3  SCORE 000000
riga  2    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~        (colonne 2-37)
riga 3-22  mappa della stanza
riga 23    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~        (colonne 2-37)
riga 24             THE MOSS GATE
```

Le colonne della riga 1:

| Colonne | Contenuto | Colore |
|---|---|---|
| 1-6 | `ENERGY` | grigio chiaro (15) |
| 8-15 | 8 × `*`, la barra dell'energia | rosso chiaro (10) / grigio scuro (11) |
| 18 | `+` icona chiave | giallo (7) |
| 19 | cifra delle chiavi | bianco (1) |
| 22 | `@` icona sigillo | verde chiaro (13) |
| 23 | cifra dei sigilli | bianco |
| 24-25 | `/3` | grigio (12) |
| 28-32 | `SCORE` | grigio chiaro |
| 34-39 | 6 cifre del punteggio | bianco |

### 7.2 Perché l'HUD si stampa una volta sola

`draw_room` scrive le righe di celle 3-22 (bitmap, screen RAM, Color RAM,
`SOLID_MAP`) e `clear_name_row` la riga 24. Le righe **0, 1, 2 e 23 non
vengono mai toccate** dal cambio di stanza. Per questo `main.asm` chiama
`print_hud` **una sola volta**, all'avvio, e l'HUD sopravvive a tutti i cambi
di stanza senza essere ridisegnato.

```asm
        jsr clear_screen
        jsr init_game           ; energia 8, chiavi 0, sigilli 0, punti 0
        jsr print_hud           ; HUD completo, a schermo spento
        jsr init_hero
        jsr enter_room
```

In `SOLID_MAP` le righe dell'HUD restano a 1 (solide), come le aveva lasciate
`clear_screen`, quindi l'esploratore non può entrarci.

### 7.3 Lo stato del gioco ([world.asm:163-168](game/src/world.asm#L163-L168))

```asm
room_slot:  .byte 0     ; row * GRID_WIDTH + column
energy:     .byte 0     ; 0 to ENERGY_MAX
key_set:    .byte 0     ; keys carried: bit 0 A, 1 B, 2 C
seals:      .byte 0     ; seals found, 0 to 3
score:      .byte 0, 0, 0   ; BCD, highest digits first
hud_dirty:  .byte 0     ; not 0: hud_update must run
```

Queste variabili stanno nel segmento del programma, non in zero page: si
leggono poche volte per frame, quindi la velocità della zero page non serve.

- `key_set` è una **maschera di bit**: ogni chiave è una chiave precisa (A, B
  o C), non un contatore.
- `score` è in **BCD** (Binary Coded Decimal): ogni nibble è una cifra
  decimale. Le cifre si stampano senza divisioni per 10, e sommare punti con
  `sed` + `adc` (modo decimale del 6502) negli step successivi darà
  direttamente il risultato in decimale.
- `hud_dirty` in questo step non è usato da nessuno: è predisposto per quando
  energia, chiavi e punteggio cambieranno.

---

## 8. Stringhe nel sorgente: `.enc "glyphs"` ([text.asm:138-155](game/src/text.asm#L138-L155))

Fino allo step 02 le stringhe (i nomi delle stanze) arrivavano già codificate
dal builder Python. L'HUD invece è scritto **direttamente nel sorgente
assembly**, e serve un modo per trasformare `"ENERGY"` nei codici dei glifi.

```asm
        .enc "glyphs"           ; crea/seleziona una codifica di 64tass
        .cdef "  ", 0           ; ' '      → 0
        .cdef "AZ", 1           ; 'A'..'Z' → 1..26
        .cdef "09", 27          ; '0'..'9' → 27..36
        .cdef "--", 37
        .cdef "::", 38
        .cdef "..", 39
        .cdef "//", 40
        .cdef "~~", 41          ; linea orizzontale
        .cdef "**", 42          ; blocco energia
        .cdef "++", 43          ; chiave
        .cdef "@@", 44          ; sigillo
        .cdef ">>", 45          ; cursore
        .enc "none"             ; torna alla codifica normale
```

`.cdef "XY", n` assegna ai caratteri da X a Y i codici consecutivi da n in poi.
Dopo `.enc "glyphs"`, ogni `.text "..."` produce i codici dei glifi invece dei
byte ASCII. La numerazione è **la stessa di `GLYPH_ORDER` in `font.py`**:
Python (nomi delle stanze) e assembly (HUD) parlano lo stesso alfabeto.

Questo blocco si trova in fondo a `text.asm` e si chiude con `.enc "none"`:
definisce la codifica senza lasciarla attiva. `hud.asm` la attiva solo intorno
ai suoi dati.

---

## 9. `print_list` e `print_at` ([text.asm:23-44](game/src/text.asm#L23-L44))

### 9.1 Il contratto di `print_text`

`print_text` non è cambiata, ma ora si usa una sua proprietà: quando esce,
**Y contiene l'offset del `TEXT_END`** della stringa appena stampata. L'uscita
avviene infatti qui:

```asm
print_char:
        ldy text_pos
        lda (text_ptr),y
        cmp #TEXT_END
        beq print_done          ; Y = posizione del $FF
```

### 9.2 `print_list`

```asm
print_list:                     ; A/Y = indirizzo della lista
        sta text_ptr
        sty text_ptr+1
list_next:
        ldy #0
        lda (text_ptr),y        ; primo byte = colonna
        cmp #TEXT_END
        beq list_done           ; una "colonna" $FF = fine della lista
        jsr print_text          ; Y = offset del suo $FF
        tya
        sec                     ; +1: salta anche il $FF
        adc text_ptr            ; text_ptr += Y + 1
        sta text_ptr
        bcc list_next
        inc text_ptr+1
        jmp list_next
list_done:
        rts
```

- **Formato della lista:** stringhe una dopo l'altra, ciascuna chiusa dal suo
  `$FF`, più un `$FF` finale **nella posizione in cui inizierebbe la stringa
  successiva**. Una colonna vale al massimo 39, quindi `$FF` come primo byte
  non è ambiguo.
- **`sec` + `adc` = somma più 1** in una sola istruzione: con il carry a 1,
  `adc` somma Y + 1. È l'idioma "puntatore = puntatore + lunghezza + 1" senza
  un `iny` separato.
- **Convenzione A/Y per gli indirizzi:** A = byte basso, Y = byte alto. È la
  stessa di molte routine del KERNAL, ed è comoda perché `lda #<lista` /
  `ldy #>lista` caricano un indirizzo a 16 bit senza toccare X.

### 9.3 `print_at`

```asm
print_at:                       ; A/Y = indirizzo di una stringa
        sta text_ptr
        sty text_ptr+1
print_text:                     ; prosegue qui (fall-through)
```

È un secondo punto d'ingresso di `print_text`, che prima imposta il puntatore.
Costa 4 byte invece di una subroutine separata.

---

## 10. I dati fissi dell'HUD: `hud_frame` ([hud.asm:107-134](game/src/hud.asm#L107-L134))

```asm
        .enc "glyphs"
hud_frame:
        .byte 1, HUD_ROW, LIGHT_GREY
        .text "ENERGY"
        .byte TEXT_END
        .byte BAR_COLUMN, HUD_ROW, LIGHT_RED
        .text "*" x ENERGY_MAX           ; operatore di ripetizione: 8 volte
        .byte TEXT_END
        ...
        .byte 2, HUD_ROW + 1, GREEN
        .text "~" x RULE_LENGTH          ; 36 linee
        .byte TEXT_END
        .byte 2, 23, GREEN               ; over the room name
        .text "~" x RULE_LENGTH
        .byte TEXT_END
        .byte TEXT_END                   ; end of the list
        .enc "none"
```

L'operatore `x` di 64tass ripete una stringa: `"*" x ENERGY_MAX` produce 8
asterischi. La barra e le linee si allungano o si accorciano cambiando una
costante.

Byte reali nel `.prg` (`hud_frame` = `$0E47`):

```
01 01 0F  05 0E 05 12 07 19  FF     col 1,  riga 1, grigio chiaro, "ENERGY"
08 01 0A  2A 2A 2A 2A 2A 2A 2A 2A  FF   col 8, rosso chiaro, 8 × '*' (42)
12 01 07  2B  FF                    col 18, giallo, '+' (43)
16 01 0D  2C  FF                    col 22, verde chiaro, '@' (44)
18 01 0C  28 1E  FF                 col 24, grigio, '/' (40) '3' (30)
1C 01 0F  13 03 0F 12 05  FF        col 28, grigio chiaro, "SCORE"
02 02 05  29 × 36  FF               col 2, riga 2, verde, 36 × '~' (41)
02 17 05  29 × 36  FF               col 2, riga 23, verde, 36 × '~'
FF                                  fine della lista
```

---

## 11. La catena `print_hud` → `hud_update` → `print_score`

Le tre routine sono scritte **una dopo l'altra senza `rts` intermedi**:

```
print_hud:    stampa hud_frame con print_list
   ↓ (fall-through)
hud_update:   colori della barra, cifra chiavi, cifra sigilli
   ↓ (fall-through)
print_score:  6 cifre del punteggio, poi rts
```

Ogni etichetta è anche un punto d'ingresso indipendente:

- `print_hud` disegna tutto, la parte fissa e i valori: si usa all'avvio;
- `hud_update` riscrive **solo i valori**: servirà quando `hud_dirty`
  segnalerà un cambiamento;
- `print_score` stampa solo il punteggio, da una colonna e una riga a scelta:
  servirà alla schermata finale.

Il chiamante sceglie quanto lavoro fare entrando a un punto diverso della
stessa sequenza.

### 11.1 La barra dell'energia: si cambia solo il colore ([hud.asm:26-39](game/src/hud.asm#L26-L39))

```asm
hud_update:
        lda #0
        sta hud_dirty           ; il lavoro è fatto
        ldx #0                  ; cella della barra 0..7
bar_cell:
        lda #DARK_GREY << 4     ; $B0: energia persa
        cpx energy
        bcs bar_colour          ; X ≥ energy → persa
        lda #LIGHT_RED << 4     ; $A0: energia presente
bar_colour:
        sta BAR_SCREEN,x        ; $4430 + X
        inx
        cpx #ENERGY_MAX
        bne bar_cell
```

I glifi `*` della barra **non cambiano mai**: sono stati stampati una volta da
`print_hud`. Il glifo usa solo il codice pixel 01, che prende il colore dal
nibble alto della screen RAM. Per "svuotare" una cella basta quindi scrivere
**un byte** in screen RAM (`$A0` → `$B0`), senza toccare gli 8 byte del
bitmap.

`BAR_SCREEN = SCREEN + HUD_ROW × 40 + BAR_COLUMN = $4400 + 40 + 8 = $4430`,
calcolato dall'assembler. L'idioma "valore di default, poi sovrascrivi se"
(`lda #DARK_GREY<<4` / `bcs` / `lda #LIGHT_RED<<4`) evita un salto nel caso
più comune.

Con `energy = 5`: celle 0-4 → `$A0` (rosse), celle 5-7 → `$B0` (grigie).

### 11.2 Il numero di chiavi: conteggio dei bit ([hud.asm:41-53](game/src/hud.asm#L41-L53))

`key_set` è una maschera; l'HUD mostra **quante** chiavi si possiedono, cioè il
numero di bit a 1 (popcount).

```asm
        lda #KEYS_COLUMN
        sta digit_text          ; colonna della cifra
        ldx #0                  ; contatore
        lda key_set
count_keys:
        beq keys_counted        ; A = 0: nessun altro bit
        lsr a                   ; bit 0 → Carry
        bcc count_keys          ; era 0: continua
        inx                     ; era 1: conta
        bcs count_keys          ; sempre preso (C = 1)
keys_counted:
        txa
        jsr print_digit
```

**Un dettaglio sottile sui flag.** `beq keys_counted` controlla il flag Z, ma Z
non viene sempre dalla stessa istruzione:

- se si arriva da `bcc`, Z viene da `lsr`, quindi riflette A: è il test giusto;
- se si arriva da `bcs` (dopo `inx`), Z viene da **`inx`**, e X ≥ 1 quindi
  Z = 0: il ciclo non esce anche se A fosse già 0.

Non è un errore: nel secondo caso il ciclo fa **un giro in più**. `lsr` di
A = 0 dà C = 0 e Z = 1, `bcc` torna a `count_keys` e `beq` esce. Il risultato
è corretto e il codice risparmia un'istruzione.

Traccia con `key_set = %101` (chiavi A e C):

| Passo | A | C | X | Z usato da `beq` |
|---|---|---|---|---|
| inizio | `101` | – | 0 | da `lda`: 0 → continua |
| `lsr` | `010` | 1 | 1 | da `inx`: 0 → continua |
| `lsr` | `001` | 0 | 1 | da `lsr`: 0 → continua |
| `lsr` | `000` | 1 | 2 | da `inx`: 0 → continua |
| `lsr` | `000` | 0 | 2 | da `lsr`: **1 → esce** |

Risultato: X = 2, e l'HUD mostra "2". `bcs count_keys` dopo `inx` funziona
come salto incondizionato perché `inx` non modifica il carry, che è 1 visto
che `bcc` non è stato preso.

### 11.3 `print_digit`: una stringa-modello che si modifica ([hud.asm:91-104](game/src/hud.asm#L91-L104))

```asm
print_digit:                    ; A = cifra 0-9
        clc
        adc #GLYPH_ZERO         ; 27: codice del glifo '0'
        sta digit_text+3        ; scrive il glifo nella stringa
        lda #<digit_text
        ldy #>digit_text
        jsr print_at
        inc digit_text          ; la prossima cifra va a destra
        rts

digit_text:
        .byte 0, HUD_ROW, WHITE, 0, TEXT_END
        ;     col  riga   colore glifo fine
```

Invece di una routine che stampa un singolo carattere, il codice riusa
`print_text` con una **stringa di un carattere costruita al volo**:

- `digit_text+0` è la colonna: la imposta il chiamante e la incrementa
  `print_digit`, quindi cifre successive vanno in celle successive;
- `digit_text+1` è la riga: vale `HUD_ROW`, ma il commento avverte che la
  schermata finale la cambierà per stampare il punteggio altrove;
- `digit_text+3` è il glifo, riscritto a ogni chiamata.

Nel `.prg` (`$0E41`) il modello è `00 01 01 00 FF`.

**Perché i chiamanti tengono i contatori in memoria.** `print_text` usa sia X
(riga) sia Y (indici). Un chiamante che contasse in X o Y lo perderebbe a ogni
cifra. Per questo `print_score` usa `score_byte`, in memoria, invece di un
registro (*"callers keep their counters in memory"*).

### 11.4 `print_score`: 3 byte BCD → 6 cifre ([hud.asm:64-83](game/src/hud.asm#L64-L83))

```asm
print_score:
        lda #0
        sta score_byte          ; byte 0, 1, 2
score_digits:
        ldx score_byte
        lda score,x
        lsr a
        lsr a
        lsr a
        lsr a                   ; nibble alto = cifra più significativa
        jsr print_digit
        ldx score_byte          ; X è stato distrutto: si ricarica
        lda score,x
        and #$0f                ; nibble basso
        jsr print_digit
        inc score_byte
        lda score_byte
        cmp #3
        bne score_digits
        rts
```

Con `score = $01 $23 $45` si stampano `0`, `1`, `2`, `3`, `4`, `5`, cioè
"012345", nelle colonne 34-39. Il BCD rende l'estrazione delle cifre banale: 4
`lsr` per la cifra alta, `and #$0F` per la bassa, nessuna divisione per 10.

L'ordine "highest digits first" (big-endian) è l'opposto della convenzione del
6502 per gli indirizzi, ma qui conviene: si stampa da sinistra a destra
scorrendo i byte in ordine.

### 11.5 Costi

| Operazione | Cicli circa | Quando |
|---|---|---|
| `print_hud` completo (~95 glifi + valori) | ~20.000 | una volta, all'avvio, a schermo spento |
| `hud_update` (8 colori + 2 cifre + 6 cifre) | ~2.300 | in questo step mai; poi solo con `hud_dirty` |
| `check_exits` senza uscita | ~20 | ogni frame |

`hud_update` costa circa il 12% di un frame: per questo non verrà eseguito ogni
frame, ma solo quando qualcosa è cambiato, ed è il motivo di `hud_dirty`.

---

## 12. Osservazioni e limiti di questo step

- **Solo 7 stanze su 16 sono raggiungibili**, tutte nella zona dell'atrio. Il
  cambio di palette di `set_zone` non si vede ancora in gioco; si vedrà quando
  le porte si apriranno.
- **Le porte fermano l'esploratore** con `hero_block = 2`, ma non c'è ancora
  nessuna logica che lo usi.
- **L'HUD è statico**: energia 8, 0 chiavi, 0 sigilli, punteggio 000000. Tutto
  il meccanismo di aggiornamento è però già pronto (`hud_update`,
  `hud_dirty`, BCD).
- **Il cambio di stanza è un flip-screen** di circa 10 frame di nero. Non c'è
  scorrimento: è il prezzo di ridisegnare ~8 KB di bitmap a ogni stanza.
- **Nessun controllo a runtime** su griglia e aperture: la correttezza è tutta
  nel builder. Se si modificasse a mano `rooms.bin` aggirando `dungeon.py`,
  un'apertura sbagliata porterebbe `room_slot` fuori dalla griglia e il
  programma disegnerebbe una pagina di memoria qualunque.
- **L'ordine in `play_frame`** (`update_hero` → `check_exits` →
  `animate_hero` → `place_hero`) fa sì che, nel frame del cambio di stanza, lo
  sprite venga posizionato solo dopo che la nuova stanza è pronta e la
  coordinata d'ingresso è già impostata.
