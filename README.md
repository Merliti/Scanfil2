# HTML-ist XML-i parser
Skript konverteerib HTML formaadis UUT raporti struktrueeritud XML failiks ja arhiveerib HTML faili käsureal etteantud (või vaikimisi kausta `arhiiv`) kausta.
Skript otsib HTML-ist vajalikud väljad, valideerib need ja salvestab need XML faili, mis salvestatakse käsureal etteantud kausta.

## Nõuded

Enne skripti käivitamist veendu, et sul on Python 3.x ja installi endale vajalik pakett:

`pip install beautifulsoup4`

## Kasutamine
Skripti käivitamiseks käsurealt:

`python script.py -d1 <path_to_html_file> -d2 <output_xml_directory> [-a <optional_archive_directory>]`

Näiteks: 
`python parser.py -d1 server/kaust1/kaust2/Failnr1.html -d2 server/kaust1/kaust3/ -a server/kaust1/arhiiv`

- `-d1` või `--dir1` (nõutud): UUT rapordi HTML faili asukoht.
- `-d2` või `--dir2` (nõutud): XML faili salvestamise asukoht/kaust.
- `-a` või `--archive` (valikuline): Arhiveerimiskausta asukoht.  Kui pole antud, siis on vaikimisi (`../arhiiv`). Kui antud kausta pole, siis see luuakse.

## Loogika

Skript on ülesehitatud UUT aruannete lugemiseks, sõelumiseks, teisendamiseks ja arhiveerimiseks. Allpool on toodud põhifunktsioonide ja nende eesmärgid:

1. Loggimine: Kuvab errorid ja üldise teabe käsureale. Et oleks lihtsam omada teavet skripti käigus tehtud toimingutest (Nt: kaustade loomine, failide ülekirjutamine)

2. `read_html_file(file_path)`: loeb määratud failist HTML-i sisu ja kontrollib, kas see sisaldab vajalikke andmeid. Kui fail on tühi või seda ei eksisteeri, logib see veateate ja tagastab väärtuse `None`

3. `prettify_xml(element)`: Muudab loodava XML faili paremini loetavaks.

4. `html_to_xml(html_content)`: Skripti põhifunktsioon:

  - Parsib HTML faili kasutades BeautifulSoup paketti.
  - Otsib HTML failist vajalikud väljad (`Station ID`, `Serial Number`, `Sequence Name`, `UUT Result`, `Date`, and `Time`).
  - Määrab `status` järgi kas "PASS" või "FAIL". Kalkuleerib `start_time` ja `end_time` kuupäevast, ajast ja täitmisaja põhjal.
  - Ehitab XML struktuuri `xml.etree.ElementTree` ja loob XML sisu.

5. `parse_args()`: seadistab käsurea argumentide käsitluse.

6. `main(args: argparse.Namespace) -> int`: Jooksutab kogu protsessi:

    - Loob sihtkoha kausta (hetkel siis `kaust2` juhuks kui seda juba ei eksisteeri).
    - Konverteerib HTML-i sisu XML-iks `html_to_xml` abil.
    - Salvestab loodud XML faili etteantud kausta.
    - Arhiveerib (liigutab) algse HTML faili etteantud arhiveerimiskausta(`../arhiiv`).

Skript logib olulisemad toimingud, et oleks lihtsam jälgida juhuks kui tekib mingi probleem.

Anomaaliad, mida skript suudab tuvastada ja lahendada või väljutada vastava teavituse:
- Kui etteantud HTML on tühi - > ERROR: Html on tühi
- Kui HTML-is pole kõiki XML faili jaoks vajalikke välju - > ERROR: x väärtus puudub
- Arhiivi kaust puudub (ja pole ka käsureal ette antud) - > LOG: Lõin vastava kausta
- XML kaust puudub - > LOG: Lõin vastava kausta
- Samanimeline XML on juba kaustas - > LOG: toimus faili ülekirjutus
- Samanimeline fail on juba arhiiv kaustas - > LOG: toimus faili ülekirjutus
