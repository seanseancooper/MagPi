# HOSTS FILE

```commandline
##
# Host Database
#
# localhost is used to configure the loopback interface
# when the system is booting.  Do not change this entry.
##
127.0.0.1       localhost
255.255.255.255 broadcasthost
::1             localhost
# 127.0.0.1       x86_64-apple-darwin13.4.0 


# Added by Docker Desktop
# To allow the same kube context to work on the host and the container:
# 127.0.0.1 kubernetes.docker.internal
# End of section

# MagPy subdomains
127.0.0.1 arx.localhost
127.0.0.1 cam.localhost
127.0.0.1 gps.localhost
127.0.0.1 wifi.localhost
127.0.0.1 trx.localhost
127.0.0.1 map.localhost
127.0.0.1 sdr.localhost
127.0.0.1 net.localhost
127.0.0.1 view.localhost
```

# PORT ASSIGNMENTS

```
127.0.0.1:5001 arx.localhost
        
        ZMQ_HOST: 127.0.0.1
        ZMQ_PORT: 5011
    
127.0.0.1:5002 cam.localhost

        VIDEO_URL_ : 10.99.77.1:80
        
        streaming_host: localhost
        streaming_port: 5102
        
        IMQ_HOST : 127.0.0.1
        IMQ_PORT : 5012

127.0.0.1:5003 xxx.localhost

127.0.0.1:5004 mcp.localhost                                <-- PLANNED, NOT YET ASSIGNED IN HOSTS

127.0.0.1:5005 map.localhost
127.0.0.1:5005 gps.localhost                                <-- MAINTAINS DOMAIN FOR GPS RESOLUTION

        MAP_HOST: localhost:5105
        ELASTIC_HOST: https://localhost:9200                <-- 9200 DO NOT CONFIGURE
        ELASTIC_DASHBOARD_URL: https://localhost:5601       <-- 5601 DO NOT CONFIGURE

        JS_GPS_HOST: localhost 
        JS_GPS_PORT: 5015
        GPS_HOST: 10.99.77.1                                <-- HARDWARE NOT CONFIGURABLE
        GPS_PORT: 80                                        <-- HARDWARE NOT CONFIGURABLE

127.0.0.1:5006 wifi.localhost

        IN_ZMQ_HOST: localhost
        IN_ZMQ_PORT: 5016

        OUT_ZMQ_HOST: localhost
        OUT_ZMQ_PORT: 5026

127.0.0.1:5007 net.localhost                            

        RMQ_HOST: localhost                             <-- DO NOT CONFIGURE
        RMQ_PORT: 15672                                 <-- DO NOT CONFIGURE

        ELASTIC_HOST: https://localhost:9200            <-- DO NOT CONFIGURE
        ELASTIC_DASHBOARD_URL: https://localhost:5601   <-- DO NOT CONFIGURE
	
127.0.0.1:5008 sdr.localhost

127.0.0.1:5009 trx.localhost

127.0.0.1:5110 view.localhost


```

## arx
    ARXSignalPoint(self, worker_id, lon, lat, sgnl)
    DATA: ZeroMQ 'frame' composed of metatdata and data

>- [DONE] ARXSignalPoint RabbitMq & ZeroMQ to ARXAudioEncoder
>- [NO] Elasticsearch mappings?
>- [XX] Processing germane to audio:back to original requirements.
>- **IDEA:** project-keyword-spotter integration? feasible? alt. solution --> MCP
>- **IDEA:** ML Models germane to audio, speech and sound analysis 
>  - 'AudioEncoder' subproject
>  - text_attribute parsing
>  - audio transcription: speech to text.
>  - vocal 'stress' analysis.
>### ARXEncoder
>````
>Category            | Feature Examples
>Frequency-based     | Center frequency, bandwidth, frequency drift
>Geolocation         | Direction of arrival (DoA), location estimates, altitude
>Behavior-based      | Emission pattern, silence periods, handoff behavior
>````

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

## config:

>- **IDEA:**: Configuration layering, global vs. module vs. class:
>- class configuration: look for a configuration file at the same level as a class (overides class fields only), named 'class.json' where class is the name of the class.
>- module configuration: look for a configuration for the module, in a dir called 'config'. This overides any 'class.json' class configuration if it exists.
>- global configuration: look for a configuration file in 'config' directory, named 'module.json': this overides module config)
>- potential benefits vs. complexity added

## lib:
>- [?] code review.
>- [?] dependecies and __init__ usage.

## map [REST]
> MapAggregator: use generic aggregator.
>- [NO] Elastic Integration:
>- [NO] Elastic pull()
>- [DONE] GPS subcomponent
>>-[DONE] MAP & GPS node process configuration: hosts, ports, jinja templates.
>- [??] WX subcomponent
>- [IP] MapAggregator refresh; read from rabbitMQ, not REST
>- [XX] Hyperspectral imaging: BLOCKED DUE TO ENVIRONMENT
>- Trilaterator: **DATA is the problem** points need ~300m separation to resolve.
>  - Can this be fixed by scaling the data?
>## gps:
>## WX [NOT STARTED]:

## mcp:
>>DOCKER STARTUP ensure the container is available and is a setting in the container startup.
>
>[??] keyword-spotter integration
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
>## CAN:
>- NOT STARTED
>## PSX [NOT STARTED]
>**IDEA:** Pyshark. Visualizations? Stats? GPT?

## sdr
> SDRSignalPoint(self, worker_id, lon, lat, sgnl, array_data=None, audio_data=None, sr=48000)

> SignalFrame(timestamp: float, duration: float, carrier_freq: float, bandwidth: float, data: np.ndarray, domain: str = "time", metadata: Optional[Dict[str, Any]] = None)

> TimeFrequencyFrame(start_time: float, duration: float, freq_min: float, freq_max: float, tf_matrix: np.ndarray, metadata: Optional[Dict[str, Any]] = None)

> - DATA: RabbitMQ for object data, ZeroMQ for arrays
>- **DONE:** A thing that looks at a block of spectrum, finds the peaks in the EM
and tunes an SDRWorker() receiver to the peak frequency, recording it as a SSET SignalFrame().
>>- **DONE:** Receiver modifications: assignable frequency, bandwidth
>>- **DONE:** Scanner modifications: integration
>>- SignalPoint processing zeroMQ
>>- ARXAudioEncoder via MQ! not a local method. offline processing...
>>- Elasticsearch mappings

>### SDRSignalAnalyzer
>```
>Category            | Feature Examples
>
>Time-based          | Pulse repetition interval (PRI), burst duration, timing jitter
>Frequency-based     | Center frequency, bandwidth, frequency drift
>Modulation          | Modulation type (AM/FM/PSK), symbol rate, coding scheme
>Power               | RSSI (signal strength), SNR (signal-to-noise ratio)
>Geolocation         | Direction of arrival (DoA), location estimates, altitude
>Behavior-based      | Emission pattern, silence periods, handoff behavior
>```
>
>
| **Interaction**                     | **Trigger**                              | **Effect**                                                                | **Notes**                                               |
| ----------------------------------- | ---------------------------------------- | ------------------------------------------------------------------------- | ------------------------------------------------------- |
| Click on a **highlighted area**     | User clicks inside a defined highlight   | Shows the `info` layer with `min_sel` and `max_sel`; enables buttons      | Current behavior; allows further interaction via popup  |
| Click outside any highlight         | User clicks non-highlighted canvas area  | Hides the `info` layer                                                    | Ensures only one highlight is interacted with at a time |


| **Interaction**                     | **Trigger**                              | **Effect**                                                                | **Notes**                                               |
| ----------------------------------- | ---------------------------------------- | ------------------------------------------------------------------------- | ------------------------------------------------------- |
| Click one of the 5 buttons in popup | User clicks a button in the info layer   | Triggers feature action (e.g., lock, delete, analyze, tune, rename)       | You’ll define button behavior later                     |
| Auto-highlight strongest peak       | On new spectrogram line update           | Automatically highlights the bin with highest magnitude                   | Good for real-time monitoring or scanning               |
| Filter peaks by threshold           | After receiving peaks from server/client | Highlights only peaks above magnitude threshold                           | Could be user-configurable or static                    |
| Filter peaks by frequency range     | User specifies or selects a freq range   | Highlights peaks within that frequency window                             | Useful for band-limited analysis                        |
| Click a signal (peak area) directly | Click event lands near a peak bin        | Creates highlight and shows `info` popup                                  | Can match nearest bin or use a proximity window         |
| Use a dedicated “Add Signal” button | Button in UI (outside canvas)            | Enables click-to-highlight mode; next canvas click creates a highlight    | More deliberate user-controlled interaction             |
| Drag to highlight a frequency range | User drags across canvas                 | Creates highlight using mouse start/end x positions → mapped to freq bins | Enables custom/manual region selection                  |
| Hover over a peak                   | Mouse hovers on a highlight              | Optional: display quick tooltip with frequency & magnitude                | Could enhance interactivity subtly                      |

>
>These features are often extracted using tools like Fourier Transforms, wavelet analysis, or cyclostationary analysis.
>## BLU [NOT STARTED]
>>- Likely to use SDR for this and not have a module.
>>- **IDEA:** features unique to 'Bluetooth' signals (special identifiers)

```
Nooelec NESDR SMArt
SKU 	100701
UPC 	0616469145864
Country of Manufacture 	United States
USB Interface IC 	RTL2832U
Tuner IC 	R820T2
Frequency Range (approximate) 	0.1MHz - 1750MHz
TCXO clock 	Yes
Antenna Connector Type 	SMA Female
Antenna Included? 	No
Remote Included? 	No
Additional Accessories 	No
```

## trx
TRXSignalPoint(self, worker_id, lon, lat, sgnl, text_data={}, audio_data=None, signal_type="object", sr=48000)
    DATA: RabbitMQ for object data, ZeroMQ for arrays
>- TRXUSBRetriever docker solution
>- TRXSerialRetriever may be kaput on Mac? Verify this.
>- TRXSignalPoint mappings
>- text_attribute/audio transcription.
>### TRXEncoder
>````
>    Category        | Feature Examples
>    
>    Geolocation     | Direction of arrival (DoA), location estimates, altitude
>    Behavior-based  | Emission pattern, silence periods, handoff behavior
>````

## view 
### [RabbitMQ/REST]
>- [  ] pull aggregation out of ViewController; put it in /aggregator/ViewAggregator.py
>- [  ] make generic aggregation ViewAggregator; make MQAggregator use the generic one ggregator
>- [DONE] Scanner, Tracker reads data over MQ & REST
>- [IP] Factor Scanner to read ALL SignalPoint types.
>- [? ] Integrate Kibana: blocker is elastic https
>- [? ] Integrate SDR: Bokeh, jupyterlite w/ matplotlib inline + custom javascript vertical waterfall served via node.
>- [? ] rename?
>>## ebs:
>>- configure text logging
>>- **IDEA:**: Speech Service client using MCP?


## wifi
    WifiSignalPoint(self, worker_id, lon, lat, sgnl, bssid=None) 
    [DONE]: REST endpoints and readlines via ZeroMQ
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


