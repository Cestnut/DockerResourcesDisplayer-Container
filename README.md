
# 1 Introduzione
Il progetto consiste nella creazione di monitor agent che permette la visualizzazione in tempo reale del consumo della CPU, della memoria e del Network I/O dei vari container in esecuzione su docker tramite interfaccia web, e il logging di tali dati.

L'applicazione è stata poi successivamente containerizzata, permettendo di avere in una singola immagine sia il software che l'ambiente necessario per la sua esecuzione.

# 2 Applicazione
Tramite l'interfaccia web si ha accesso a due pagine principali.
## 2.1 /
La pagina principale, consiste in una tabella con ID, CPU, Memoria e Network I/O dei container, che viene aggiornata periodicamente da uno script AJAX, attraverso chiamate alla pagina /table.

A ogni chiamata di /table vengono aggiornati i file di log, includendo i relativi timestamp.

## 2.2 /containers
Pagina che ritorna un JSON contenente tutte le statistiche dei container, indicizzate tramite il loro ID.

Inoltre è possibile effettuare una richiesta GET, specificando come attributo ID l'id del container di cui si vogliono ottenere i dati.

# 3 Container
I container sono delle unità eseguibili di software in cui viene impacchettato il codice applicativo, insieme alle sue librerie e dipendenze, con modalità comuni in modo da poter essere eseguito ovunque, sia su desktop che su IT tradizionale o cloud. 

Docker è una delle piattaforme che permette di creare, gestire ed eseguire container e immagini, utilizzata dal seguente progetto. 

È importante fare la distinzione tra immagine e container; per analogia con la programmazione a oggetti, un'immagine è una classe e un container una sua istanza. 

Quindi è l'immagine l'unità fondamentale di questa tecnologia che viene costruita e condivisa, da cui è possibile eseguire più di un container. 

Per costruire un immagine con Docker si parte dal Dockerfile, che contiene tutti i comandi necessari per assemblare l'immagine. 

# 4 Dockerfile
Il dockerfile ha una struttura a livelli, che contiene l’indicazione di comandi, librerie da utilizzare e dipendenze da importare.

Può succedere che alcuni livelli siano presenti in più progetti garentendo riutilizzo dei livelli già scaricati e di conseguenza un'ottimizzazione delle performance e dello spazio fisico utilizzato.

Il dockerfile utilizzato per buildare l'immagine è il seguente:

```
FROM python:3.8-slim-buster
WORKDIR /python-docker
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
RUN mkdir resource_logs
COPY . .
CMD [ "python3", "script.py"]
EXPOSE 5000/tcp
```

Di seguito verrà illustrato il significato di ogni comando

- FROM: Inizializza una fase di building e e imposta l'immagine di base da importare e che verrà usata dalle seguenti istruzioni. Ogni Dockerfile valido deve iniziare con l'istruzione FROM. L'immagine specificata deve essere valida e può esistere sia in locale tra le immagini già esistenti che nelle Repository pubbliche.

- WORKDIR: Imposta la directory attiva dei comandi RUN, CMD, ENTRYPOINT che seguono. Se la directory non esiste viene creata.

- COPY: Copia i nuovi file dalla cartella sorgente (la prima specificata) alla cartella destinazione all'interno del container (la seconda).

- RUN: Esegue qualunque comando sull'immagine che è stata buildata fino a quel punto e crea una nuova immagine, sulla quale verranno eseguiti i comandi successivi del Dockerfile.

- CMD: Fornisce il comando di default che verrà eseguito dalla shell una volta avviato il container. Può esserci solo un CMD per Dockerfile.

- EXPOSE: Serve per specificare a quale porta l'utente che utilizza l'immagine deve fare il binding. Non viene esposta in fase di building ma va appunto esposta durante l'esecuzione del container con la flag -p.

# 5 Utilizzo
Una volta creata l'immagine, per il corretto funzionamento del software è necessario montare la socket del demone Docker ed effettuare il binding della porta.

Sarà quindi possibile accedere al container tramite interfaccia web, vedendo una tabella con ID, nome, utilizzo CPU e utilizzo memoria che si aggiornano in tempo reale.

## 5.1 Montare la cartella con i file di log
### 5.1.1 Motivazione

Va montata la cartella che contiene i log già esistenti, o su cui si vuole vengano salvati i nuovi log, per rendere persistenti i dati creati all'interno del container.

### 5.1.1 Flag

Il percorso che viene utilizzato all'interno del container è /python-docker/resource_logs.
L'opzione da aggiungere quindi è:

```
-v percorso_della_cartella_dei_log:/python-docker/resource_logs
```

## 5.2 Usare Docker da dentro il containter

### 5.2.1 Montare la socket di docker
Per fare ciò basta fare montare il file docker.sock nel percorso all'interno del container in cui di default si trova la socket, cioè /var/run/docker.sock. L'opzione da aggiungere quindi è:

```
-v percorso_della_socket:/var/run/docker.sock
```

Ciò chiaramente comporta un notevole assottigliamento della sicurezza fornita dal container, in quanto il demone Docker è in esecuzione sull'host con i permessi di root.

Quindi nel caso in cui dovesse esserci una vulnerabilità sia nel software all'interno del container che nel demone, sarebbe possibile effettuare un attacco ai danni dell'host stesso.

### 5.2.2 Alternativa: --privileged
Un altro modo per rendere la socket dell'host di docker accessibile all'interno del container sarebbe l'utilizzo della flag --privileged, durante la fase di run.

Questo comando monta automaticamente dock.sock nel percorso predefinito, ma in più il container ottiene maggiori privilegi incluso ad esempio l'accesso a tutti i dispositivi sull'host, rendendo quindi possibile montare il filesystem dell'host, e poterlo leggere e modificare a piacimento dato che Docker esegue con i permessi di root.

### 5.2.3 Differenze
Nonostante il secondo approccio possa sembrare più rischioso in caso qualcuno riesca ad accedere al container, in realtà la differenza è nulla.

Infatti una volta montata la socket, oltre a poter leggere i dati dei container come nel caso dell'applicazione descritta in questo testo, è possibile anche creare container, includendo la flag --privileged, per poi accedervi dall'interno del container stesso

## 5.3 Binding della porta
### 5.3.1 Motivazione
Effettuare il binding di una porta è necessario per potersi connettere alla porta all'interno del container in cui il server è in ascolto.
### 5.3.2 Flag
La porta in cui il server è in ascolto è la 5000, quindi basta scegliere una qualsiasi porta libera e bindarla a quella. L'opzione quindi è:

```
-p porta_scelta:5000
```

## 5.4 Comando
I comandi completi per eseguire correttamente il container sono:

```
$ docker run -p porta_scelta:5000 -v percorso_della_socket:/var/run/docker.sock  \
-v percorso_cartella_dei_log:/python-docker/resource_logs nomeImmagine

```

oppure,

```
$ docker run -p porta_scelta:5000 \
-v percorso_cartella_dei_log:/python-docker/resource_logs --privileged nomeImmagine
```

# 6 Codice
Il software è stato realizzato in Python, utilizzando il framework Flask per costruire l'interfaccia web, e il modulo docker per interagire con il demone Docker.

Il codice dell'applicazione è disponibile su GitHub.
Vediamo ora la parte fondamentale del codice:

```
client = docker.from_env()
containers = []
        for container in client.containers.list():
                container_stats = container.stats(stream=False)
                derived_container_stats = compute_container_stats(container_stats)
                derived_container_stats['id'] = container_stats['id']
                containers.append(derived_container_stats)
                write_log(derived_container_stats)

        return render_template('resource_table.html', containers=containers)
        
        def compute_container_stats(container_stats):
        name = container_stats['name']
       	cpu = calculate_cpu_percent(container_stats['cpu_stats'], container_stats['precpu_stats'])
        memory = calculate_memory_percent(container_stats['memory_stats'])
        network_in, network_out = calculate_network_in_out(container_stats['networks']) 

        return dict({"name": name, "cpu":cpu, "memory":memory, "network_in":network_in, "network_out":network_out})
```

Viene dapprima inizializzata una variabile client che si connette alla socket di docker.

Vengono poi listati a uno a uno tutti i container, mandandoli in input alla funzione compute_container_stats() che ne prende i campi: name, id e passando alla funzione calculate_cpu_percent() i campi cpu_stats e precpu_stats, alla funzione calculate_memory_percent() il campo memory_stats e a calculate_network_in_out() il campo networks

Verranno di seguito illustrate nello specifico le funzioni per il calcolo delle risorse.

## Formula calcolo utilizzo CPU
Di seguito verrà inserita la funzione direttamente dal codice, e poi spiegato cosa viene calcolato effettivamente ad ogni passaggio.[^CPUFormula]

[^CPUFormula]: [CPU usage Formula](https://gist.github.com/BeardedDonut/5e3643b06e90ce4d41197d8cfb8fb0b5)

```
def calculate_cpu_percent(cpu_stats, precpu_stats):
    cpu_count = cpu_stats["online_cpus"]
    cpu_percent = 0.0
    cpu_delta = float(cpu_stats["cpu_usage"]["total_usage"]) - float(precpu_stats["cpu_usage"]["total_usage"])
    system_delta = float(cpu_stats["system_cpu_usage"]) - float(precpu_stats["system_cpu_usage"])
    if system_delta > 0.0:
       cpu_percent = cpu_delta / system_delta * 100.0 * cpu_count
    return round(cpu_percent,2)
```

Innanzitutto chiariamo la distinzione tra cpu_stats e precpu_stats.

Le prime sono le ultime statistiche della cpu calcolate, le seconde sono invece quelle riguardanti il calcolo ancora prima.

Questo perché i dati salvati riguardo l'utilizzo in nanosecondi dall'inizio del monitoraggio dei dati (e non solo dell'ultimo tick), è quindi necessario calcolarne la variazione.

Vediamo infatti che viene calcolata la variazione dell'utilizzo della cpu del container (cpu_delta) e poi la variazione dell'utilizzo della cpu da parte dell'intero sistema (system_delta) inclusi l'utilizzo in idle, da parte del kernel e da parte dell'utente.

Viene infine calcolata la percentuale, moltiplicando per il numero di cpu (cpu_count). Quest ultimo fatto implica che è possibile vedere consumi superiori al 100% (Il 100% indica quindi che l'equivalente di una tra le CPU disponibili è completamente utilizzata)[^CPUPercentageOver100]

[^CPUPercentageOver100]: [Why can CPU usage be over 100](https://github.com/moby/moby/issues/13626#issuecomment-107522479)

## 6.1 Formula calcolo utilizzo memoria

```
def calculate_memory_percent(memory_stats):
   return round(float(memory_stats['usage'])/float(memory_stats['limit'])*100,2)
```

In questa formula viene semplicemente preso in considerazione l'utilizzo di memoria corrente del container (usage) e il limite di memoria della macchina[^MemoryFormula] (oltre il quale si andrebbe in Out Of Memory).

[^MemoryFormula]: [Memory Usage Formula](https://github.com/moby/moby/blob/eb131c5383db8cac633919f82abad86c99bffbe5/cli/command/container/stats_helpers.go#L110)

## 6.2 Formula calcolo Network I/O

```
def calculate_network_in_out(container_stats):
        conversion_costant = 1024
        network_in = 0
        network_out = 0 
        for interface in container_stats['networks']:
                network_in += container_stats["networks"][interface]['rx_bytes']
                network_out += container_stats["networks"][interface]['tx_bytes']

        return network_in/conversion_costant, network_out/conversion_costant
```

Vengono contati i byte in ingresso e uscita da ogni interfaccia. Viene ritornato il risultato diviso per una costante di conversione, che in questo caso converte in kB.
