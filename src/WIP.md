# "Never give up on code."

## arx
    ARXSignalPoint(self, worker_id, lon, lat, sgnl)
    DATA: ZeroMQ 'frame' composed of metatdata and data

>- [DONE] ARXSignalPoint RabbitMq & ZeroMQ to ARXAudioEncoder
>- [XX] Elasticsearch mappings?
>- [XX] Processing germane to audio:back to original requirements + new **IDEA:**s.
>- **IDEA:** project-keyword-spotter integration? feasible? alt. solution --> MCP
>- **IDEA:** ML Models germane to audio, speech and sound analysis 
>  - 'AudioEncoder' subproject
>  - text_attribute parsing
>  - audio transcription: speech to text.
>  - vocal 'stress' analysis.
### ARXEncoder
````
Category            | Feature Examples
Frequency-based     | Center frequency, bandwidth, frequency drift
Geolocation         | Direction of arrival (DoA), location estimates, altitude
Behavior-based      | Emission pattern, silence periods, handoff behavior
````


## BLU [NOT STARTED]
>- Likely to use SDR for this and not have a module.
>- **IDEA:** features unique to 'Bluetooth' signals (special identifiers)

## cam
    FrameObjekt()
    DATA: RabbitMQ 'message' for object data, ImageMQ frame for images
>- Automate FrameObjektTracker output analysis:. Design a processing chain based on MQ.
>>- [IP] Encoding frames using FrameObjektEncoder: what fields are encoded, and how analyzed.
>>- [? ] models @ huggingface.
>>- [DONE] ImageZMQ messaging now passes FrameObjekt
>>- [??] FrameObjekt encoder needs a processing queue.
>>- [? ] FrameObjektEncoder Elasticsearch mappings
>- Integrate a Wifi security IR camera as secondary source.
>- overlay processed IR images as outlines (see in the dark)
>- Integrate a hardware camera as tertiary source;
>- perhaps a magnifiged ROI/license plate reader?
>- Camera switching?

## CAN:
>- NOT STARTED

## config:

>- **IDEA:**: Configuration layering, global vs. module vs. class:
>- class configuration: look for a configuration file at the same level as a class (overides class fields only), named 'class.json' where class is the name of the class.
>- module configuration: look for a configuration for the module, in a dir called 'config'. This overides any 'class.json' class configuration if it exists.
>- global configuration: look for a configuration file in 'config' directory, named 'module.json': this overides module config)
>- potential benefits vs. complexity added

## ebs:
>- configure text logging
>- **IDEA:**: Speech Service client using MCP?

## gps: now a MAP submodule

## lib:
>- [?] code review.
>- [?] dependecies and __init__ usage.

## map 
MapAggregator: read configs, test REST endpoints and pull data
>- [NO] Elastic Integration:
>- [NO] Elastic pull()
>- [DONE] GPS subcomponent
>>- MAP & GPS node process configuration: hosts, ports, jinja templates.
>- [??] WX subcomponent
>- [IP] MapAggregator refresh; read from rabbitMQ, not REST
>- [XX] Hyperspectral imaging: BLOCKED DUE TO ENVIRONMENT
>- Trilaterator: **DATA is the problem** points need ~300m separation to resolve.
>  - Can this be fixed by scaling the data?

## mcp:
DOCKER STARTUP ensure the container is available and is a setting in the container startup.

[??] keyword-spotter integration
>### Pattern Learning
> Use statistical or ML models to find structure:
>>- Clustering: Find recurring emission types or behaviors (DBSCAN, k-means)
>>- Classification: Identify known emitters or mission profiles
>>- Sequence modeling: Use HMMs or LSTMs to learn time-based sequences of events
>>- Anomaly detection: Spot rare or covert behavior
>### Prediction & Inference
>Once models learn normal behavior:
>>- Predict next signal in a sequence
>>- Infer emitter identity or intent
>>- Detect prep for operations or movement
>>- Spot spoofing or jamming attempts
>### Temporal Event Sequences
>Use time-series to model:
>>- Emission patterns
>>- Inter-event intervals (e.g., radar → data uplink → artillery)
>### Probabilistic Inference Engine
>>-  Apply Markov Chains or Bayesian Networks to model expected vs. unexpected sequences
>>-  Anomaly detection for spotting new patterns (e.g., movement prep)

# net:
>- [DONE] Directory structure for ElasticSearch assets.
>- ElasticSearch data mapping. Dense vectors, nested data, types
> > what about EAVs, object/NoSQL?
>- Dashboard URL in template: too where/what?
>- MCP integration with LLM: pass data and prompts to LLM, have it generate results as JSON data
> >- direct manipulation of internal mappings?
> >- augmented data (extra rows in tables, overlay symbology in maps
>- - AR in CAM module?

## PSX [NOT STARTED]
**IDEA:** Pyshark. Visualizations? Stats? GPT?

## sdr
    SDRSignalPoint(self, worker_id, lon, lat, sgnl, array_data=None, audio_data=None, sr=48000)
    DATA: RabbitMQ for object data, ZeroMQ arrays
>- ****IDEA:**:** A thing that looks at a block of spectrum, finds the peaks in the EM
and tunes an SDRWorker() receiver to the peak frequency, recording it as a Signal().
>>- Receiver modifications: assignable frequency, bandwidth
>>- [IP] Scanner modifications: integration
>>- SignalPoint processing zeroMQ
>>- ARXAudioEncoder via MQ! not a local method. offline processing...
>>- Elasticsearch mappings

### SDRSignalAnalyzer
```
Category            | Feature Examples

Time-based          | Pulse repetition interval (PRI), burst duration, timing jitter
Frequency-based     | Center frequency, bandwidth, frequency drift
Modulation          | Modulation type (AM/FM/PSK), symbol rate, coding scheme
Power               | RSSI (signal strength), SNR (signal-to-noise ratio)
Geolocation         | Direction of arrival (DoA), location estimates, altitude
Behavior-based      | Emission pattern, silence periods, handoff behavior
```
>These features are often extracted using tools like Fourier Transforms, wavelet analysis, or cyclostationary analysis.

## trx
    TRXSignalPoint(self, worker_id, lon, lat, sgnl, text_data={}, audio_data=None, signal_type="object", sr=48000)
    DATA: RabbitMQ for object data, ZeroMQ for arrays
>- TRXUSBRetriever docker solution
>- TRXSerialRetriever may be kaput on Mac? Verify this.
>- TRXSignalPoint mappings
>- text_attribute/audio transcription.

### TRXEncoder
````
    Category        | Feature Examples
    
    Geolocation     | Direction of arrival (DoA), location estimates, altitude
    Behavior-based  | Emission pattern, silence periods, handoff behavior
   ````

## view 
### ViewController [RabbitMQ/REST]
>- [DONE] Reads WIFI data over MQ & REST
>- [DONE] Scanner, Tracker reads data over MQ & REST
>- [IP] Factor Scanner to read ALL SignalPoint types.
>- [? ] Integrate Kibana: blocker is elastic https
>- [? ] Integrate SDR: Bokeh, jupyterlite w/ matplotlib inline + custom javascript vertical waterfall served via node.
>- [? ] rename?

## WX [NOT STARTED]:
>- Likely Subcomponent of MAP

## wifi
    WifiSignalPoint(self, worker_id, lon, lat, sgnl, bssid=None) 
    DATA: REST endpoints and readlines via RabbitMQ
- Produces and reads data over REST & MQ

```
Category        | Feature Examples
Power           | RSSI (signal strength), SNR (signal-to-noise ratio)
Geolocation     | Direction of arrival (DoA), location estimates, altitude
Behavior-based  | Emission pattern, silence periods, handoff behavior
```

---
## DOCKER:
>- TRX:docker_trx: dockerfile and compose update: works, add spice where needed.
>- NET:docker_elastic: dockerfile and compose updates: works, add spice where needed.
>->-  HTTPS for Kibana:
>->- >-  docker-compose.yaml for cluster appears to have certs and password is in env. It may be the case that it
>->- >-  needs to be enabled and configured in the compose file.
>->-  Kibana dashboards: component to read serialized json output on filesystem.
>- NET:docker_rabbitMQ: dockerfile and compose updates: works, add spice where needed.
---
## SignalPoint Hierarchy [DESIGN IN PROGRESS]:
### Signal Typing & Labeling
>>#### Label signals by type:
>>- RADAR (pulse, FMCW, doppler): How do these signals appear as data? ndarray? vector?
>>- COMMS (voice, digital, burst)
>>- NAV (e.g., beacons, GPS)
>>- UNKNOWN: Deceptive/jamming patterns ( types don't support periodic data; Worker() will do this. )

> **IDEA:** label 'types' by signal: what frequencies is that thing putting out? what data type is this?

>#### Signal: text attributes
>#### SignalPoint: (self, lon, lat, sgnl)
>- **ARXSignalPoint**:  Continuous Recorded Audio Data, [COMMS]
>- **SDRSignalPoint**:  Text attributes, Structured Array/Object data [NAV, COMMS]
>- XRXSignalPoint: (pulse, FM Carrier Wave, doppler) Near SignalPoint type for 'radar'.
>- **TRXSignalPoint**:  Text attributes and ARXSignalPoint Data [COMMS]
>- **WifiSignalPoint**: Continuous Vector Signal data [COMMS]
>- **FrameObjekt**: CAM Image Container.

>>#### Signal Sources as "Agents" -- **IDEA:**: see Worker(), SSET/Signal Semiotics
>>- Each emitter can be modeled as an agent with:
>>- Location (lat, lon)
>>- Emission type (radar, voice, data)
>>- Repetition pattern (period, schedule, timing -- temporal data): Some types don't support periodic data
>>- Signal fingerprint (modulation, bandwidth, power, etc.)

>- You could treat these like “classes” for supervised ML, or cluster them for unsupervised pattern discovery.
### Spectral Analysis Features to Extract for Each SignalPoint type [scipy.signal, numpy.fft]:
````
Feature                         : Description

Mean signal power               : Average strength
Variance                        : Signal stability
FFT Peak/Dominant Frequency>-   : Periodic behavior
Auto-correlation lag            : Repetitions
Coherence with other signals    : Time-dependent similarity
Rolling correlation window      : Pairwise time-varying relationships [pandas.rolling().corr()]
Mean signal power               : Average strength
-----------------------------------------------------------------------------------------------
PCA / UMAP                      | sklearn, umap-learn
Clustering                      | sklearn.cluster
Mutual Information              | sklearn.metrics.mutual_info_score


