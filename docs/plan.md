# Documentation plan/structure

## Quickstart

## App, LabThing, and Server

* create_app
* LabThing class
* Server class
* current_labthing

### HTTP API structure

* Thing Description (root)
* Swagger-UI
* Action queue
* Extension list

### WebSocket API structure

* Not yet implemented

### Serialising data

* fields
* schema
* semantics

### Action tasks

* Preamble (all actions are tasks, etc)
* Labthing.actions TaskPool
* current_task
* update_task_progress
* update_task_data
* Stopping tasks
  * TaskThread.stopped event
  * TaskKillException

### Synchronisation

* StrictLock
* CompositeLock
* ClientEvent

## Advanced usage

### View classes

* labthings.views
  
### Components

* Access to Python objects by name
  * Used to access hardware from within Views
* registered_components, find_component

### Encoders

* labthings.json.LabThingsJSONEncoder

### Extensions

* labthings.extensions.BaseExtension
* labthings.extensions.find_extensions
* registered_extensions, find_extension