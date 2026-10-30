# FHIR Reference

FHIR REST, SQL, authentication, resource builders, mapping, and defensive extraction helpers.

For workflow context, see [FHIR module guide](../modules/fhir.md).

## Functions And Classes

- [`fyron.fhir.auth.Auth`](#fyronfhirauthauth)
- [`fyron.fhir.auth.Auth.client_credentials`](#fyronfhirauthauthclientcredentials)
- [`fyron.fhir.auth.Auth.token_env`](#fyronfhirauthauthtokenenv)
- [`fyron.fhir.auth.Auth.close`](#fyronfhirauthauthclose)
- [`fyron.fhir.auth.TokenAuth`](#fyronfhirauthtokenauth)
- [`fyron.fhir.auth.TokenAuth.is_refresh_required`](#fyronfhirauthtokenauthisrefreshrequired)
- [`fyron.fhir.auth.now_utc`](#fyronfhirauthnowutc)
- [`fyron.fhir.builder.attachment`](#fyronfhirbuilderattachment)
- [`fyron.fhir.builder.build_bundle`](#fyronfhirbuilderbuildbundle)
- [`fyron.fhir.builder.build_condition`](#fyronfhirbuilderbuildcondition)
- [`fyron.fhir.builder.build_diagnostic_report`](#fyronfhirbuilderbuilddiagnosticreport)
- [`fyron.fhir.builder.build_document_reference`](#fyronfhirbuilderbuilddocumentreference)
- [`fyron.fhir.builder.build_encounter`](#fyronfhirbuilderbuildencounter)
- [`fyron.fhir.builder.build_endpoint`](#fyronfhirbuilderbuildendpoint)
- [`fyron.fhir.builder.build_imaging_measurement_bundle`](#fyronfhirbuilderbuildimagingmeasurementbundle)
- [`fyron.fhir.builder.build_imaging_study_reference`](#fyronfhirbuilderbuildimagingstudyreference)
- [`fyron.fhir.builder.build_llm_extraction_bundle`](#fyronfhirbuilderbuildllmextractionbundle)
- [`fyron.fhir.builder.build_medication_statement`](#fyronfhirbuilderbuildmedicationstatement)
- [`fyron.fhir.builder.build_model_device`](#fyronfhirbuilderbuildmodeldevice)
- [`fyron.fhir.builder.build_observation`](#fyronfhirbuilderbuildobservation)
- [`fyron.fhir.builder.build_observation_component`](#fyronfhirbuilderbuildobservationcomponent)
- [`fyron.fhir.builder.build_procedure`](#fyronfhirbuilderbuildprocedure)
- [`fyron.fhir.builder.build_provenance`](#fyronfhirbuilderbuildprovenance)
- [`fyron.fhir.builder.build_service_request`](#fyronfhirbuilderbuildservicerequest)
- [`fyron.fhir.builder.build_specimen`](#fyronfhirbuilderbuildspecimen)
- [`fyron.fhir.builder.codeable_concept`](#fyronfhirbuildercodeableconcept)
- [`fyron.fhir.builder.coding`](#fyronfhirbuildercoding)
- [`fyron.fhir.builder.dicom_code`](#fyronfhirbuilderdicomcode)
- [`fyron.fhir.builder.icd10`](#fyronfhirbuildericd10)
- [`fyron.fhir.builder.identifier`](#fyronfhirbuilderidentifier)
- [`fyron.fhir.builder.loinc`](#fyronfhirbuilderloinc)
- [`fyron.fhir.builder.quantity`](#fyronfhirbuilderquantity)
- [`fyron.fhir.builder.read_fhir_json`](#fyronfhirbuilderreadfhirjson)
- [`fyron.fhir.builder.reference`](#fyronfhirbuilderreference)
- [`fyron.fhir.builder.snomed`](#fyronfhirbuildersnomed)
- [`fyron.fhir.builder.summarize_fhir_bundle`](#fyronfhirbuildersummarizefhirbundle)
- [`fyron.fhir.builder.summarize_fhir_resource`](#fyronfhirbuildersummarizefhirresource)
- [`fyron.fhir.builder.ucum_quantity`](#fyronfhirbuilderucumquantity)
- [`fyron.fhir.builder.validate_fhir_bundle`](#fyronfhirbuildervalidatefhirbundle)
- [`fyron.fhir.builder.validate_fhir_references`](#fyronfhirbuildervalidatefhirreferences)
- [`fyron.fhir.builder.validate_fhir_resource`](#fyronfhirbuildervalidatefhirresource)
- [`fyron.fhir.builder.write_fhir_json`](#fyronfhirbuilderwritefhirjson)
- [`fyron.fhir.mapping.build_bundle_from_dataframe`](#fyronfhirmappingbuildbundlefromdataframe)
- [`fyron.fhir.mapping.build_conditions_from_dataframe`](#fyronfhirmappingbuildconditionsfromdataframe)
- [`fyron.fhir.mapping.build_document_references_from_dataframe`](#fyronfhirmappingbuilddocumentreferencesfromdataframe)
- [`fyron.fhir.mapping.build_imaging_measurements_from_dataframe`](#fyronfhirmappingbuildimagingmeasurementsfromdataframe)
- [`fyron.fhir.mapping.build_observations_from_dataframe`](#fyronfhirmappingbuildobservationsfromdataframe)
- [`fyron.fhir.mapping.extract_coding_summary`](#fyronfhirmappingextractcodingsummary)
- [`fyron.fhir.mapping.fhir_validation_report`](#fyronfhirmappingfhirvalidationreport)
- [`fyron.fhir.mapping.read_fhir_mapping`](#fyronfhirmappingreadfhirmapping)
- [`fyron.fhir.mapping.validate_coding_systems`](#fyronfhirmappingvalidatecodingsystems)
- [`fyron.fhir.mapping.validate_fhir_mapping`](#fyronfhirmappingvalidatefhirmapping)
- [`fyron.fhir.mapping.validate_fhir_mapping_result`](#fyronfhirmappingvalidatefhirmappingresult)
- [`fyron.fhir.mapping.validate_fhir_payload`](#fyronfhirmappingvalidatefhirpayload)
- [`fyron.fhir.mapping.write_fhir_mapping`](#fyronfhirmappingwritefhirmapping)
- [`fyron.fhir.path_presets.get_fhir_path_preset`](#fyronfhirpathpresetsgetfhirpathpreset)
- [`fyron.fhir.rest.FHIRRestClient`](#fyronfhirrestfhirrestclient)
- [`fyron.fhir.rest.FHIRRestClient.close`](#fyronfhirrestfhirrestclientclose)
- [`fyron.fhir.rest.FHIRRestClient.fetch_bundles`](#fyronfhirrestfhirrestclientfetchbundles)
- [`fyron.fhir.rest.FHIRRestClient.fetch_bundles_parallel`](#fyronfhirrestfhirrestclientfetchbundlesparallel)
- [`fyron.fhir.rest.FHIRRestClient.fetch_bundles_partitioned`](#fyronfhirrestfhirrestclientfetchbundlespartitioned)
- [`fyron.fhir.rest.FHIRRestClient.bundles_to_dataframe`](#fyronfhirrestfhirrestclientbundlestodataframe)
- [`fyron.fhir.rest.FHIRRestClient.query_to_dataframe_partitioned`](#fyronfhirrestfhirrestclientquerytodataframepartitioned)
- [`fyron.fhir.rest.FHIRRestClient.query_to_dataframe`](#fyronfhirrestfhirrestclientquerytodataframe)
- [`fyron.fhir.rest.FHIRRestClient.query_from_dataframe`](#fyronfhirrestfhirrestclientqueryfromdataframe)
- [`fyron.fhir.rest.FHIRRestClient.query_df`](#fyronfhirrestfhirrestclientquerydf)
- [`fyron.fhir.rest.FHIRRestClient.search_df`](#fyronfhirrestfhirrestclientsearchdf)
- [`fyron.fhir.rest.FHIRRestClient.query_df_partitioned`](#fyronfhirrestfhirrestclientquerydfpartitioned)
- [`fyron.fhir.rest.FHIRRestClient.search_df_partitioned`](#fyronfhirrestfhirrestclientsearchdfpartitioned)
- [`fyron.fhir.rest.FHIRRestClient.query_df_from`](#fyronfhirrestfhirrestclientquerydffrom)
- [`fyron.fhir.rest.FHIRRestClient.search_df_from`](#fyronfhirrestfhirrestclientsearchdffrom)
- [`fyron.fhir.rest.FHIRRestClient.bundles_to_df`](#fyronfhirrestfhirrestclientbundlestodf)
- [`fyron.fhir.rest.FHIRRestClient.create_resource`](#fyronfhirrestfhirrestclientcreateresource)
- [`fyron.fhir.rest.FHIRRestClient.update_resource`](#fyronfhirrestfhirrestclientupdateresource)
- [`fyron.fhir.rest.FHIRRestClient.submit_bundle`](#fyronfhirrestfhirrestclientsubmitbundle)
- [`fyron.fhir.rest.FHIRWriteResult`](#fyronfhirrestfhirwriteresult)
- [`fyron.fhir.rest.QueryJob`](#fyronfhirrestqueryjob)
- [`fyron.fhir.rest.RepeatedParam`](#fyronfhirrestrepeatedparam)
- [`fyron.fhir.rest.ResponseCache`](#fyronfhirrestresponsecache)
- [`fyron.fhir.rest.ResponseCache.get`](#fyronfhirrestresponsecacheget)
- [`fyron.fhir.rest.ResponseCache.set`](#fyronfhirrestresponsecacheset)
- [`fyron.fhir.rest.build_partition_params`](#fyronfhirrestbuildpartitionparams)
- [`fyron.fhir.rest.flatten_data`](#fyronfhirrestflattendata)
- [`fyron.fhir.rest.parse_fhir_path`](#fyronfhirrestparsefhirpath)
- [`fyron.fhir.sql.FHIRSQLClient`](#fyronfhirsqlfhirsqlclient)
- [`fyron.fhir.sql.FHIRSQLClient.close`](#fyronfhirsqlfhirsqlclientclose)
- [`fyron.fhir.sql.FHIRSQLClient.query`](#fyronfhirsqlfhirsqlclientquery)
- [`fyron.fhir.sql.FHIRSQLClient.query_to_dataframe`](#fyronfhirsqlfhirsqlclientquerytodataframe)
- [`fyron.fhir.sql.FHIRSQLClient.query_df`](#fyronfhirsqlfhirsqlclientquerydf)
- [`fyron.fhir.sql.FHIRSQLClient.query_df_partitioned`](#fyronfhirsqlfhirsqlclientquerydfpartitioned)
- [`fyron.fhir.sql.FHIRSQLClient.query_df_stream`](#fyronfhirsqlfhirsqlclientquerydfstream)
- [`fyron.fhir.sql.FHIRSQLClient.export_query_partitioned`](#fyronfhirsqlfhirsqlclientexportquerypartitioned)
- [`fyron.fhir.sql.FHIRSQLClient.query_df_parallel`](#fyronfhirsqlfhirsqlclientquerydfparallel)
- [`fyron.fhir.sql.FHIRSQLClient.query_df_for_keys`](#fyronfhirsqlfhirsqlclientquerydfforkeys)
- [`fyron.fhir.sql.FHIRSQLClient.query_from_dataframe`](#fyronfhirsqlfhirsqlclientqueryfromdataframe)
- [`fyron.fhir.sql.FHIRSQLClient.query_df_from`](#fyronfhirsqlfhirsqlclientquerydffrom)
- [`fyron.fhir.sql.SQLConfig`](#fyronfhirsqlsqlconfig)
- [`fyron.fhir.sql.SQLPartition`](#fyronfhirsqlsqlpartition)
- [`fyron.fhir.sql.build_sql_partitions`](#fyronfhirsqlbuildsqlpartitions)
- [`fyron.fhir.types.FHIRObj`](#fyronfhirtypesfhirobj)
- [`fyron.fhir.types.FHIRObj.to_json`](#fyronfhirtypesfhirobjtojson)
- [`fyron.fhir.types.FHIRObj.to_dict`](#fyronfhirtypesfhirobjtodict)
- [`fyron.fhir.utils.extract_condition`](#fyronfhirutilsextractcondition)
- [`fyron.fhir.utils.extract_diagnostic_report`](#fyronfhirutilsextractdiagnosticreport)
- [`fyron.fhir.utils.extract_encounter`](#fyronfhirutilsextractencounter)
- [`fyron.fhir.utils.extract_imaging_study`](#fyronfhirutilsextractimagingstudy)
- [`fyron.fhir.utils.extract_observation`](#fyronfhirutilsextractobservation)
- [`fyron.fhir.utils.extract_patient`](#fyronfhirutilsextractpatient)
- [`fyron.fhir.utils.extract_procedure`](#fyronfhirutilsextractprocedure)
- [`fyron.fhir.utils.process_condition_bundle`](#fyronfhirutilsprocessconditionbundle)
- [`fyron.fhir.utils.process_diagnostic_report_bundle`](#fyronfhirutilsprocessdiagnosticreportbundle)
- [`fyron.fhir.utils.process_encounter_bundle`](#fyronfhirutilsprocessencounterbundle)
- [`fyron.fhir.utils.process_imaging_study_bundle`](#fyronfhirutilsprocessimagingstudybundle)
- [`fyron.fhir.utils.process_observation_bundle`](#fyronfhirutilsprocessobservationbundle)
- [`fyron.fhir.utils.process_patient_bundle`](#fyronfhirutilsprocesspatientbundle)
- [`fyron.fhir.utils.process_procedure_bundle`](#fyronfhirutilsprocessprocedurebundle)
- [`fyron.fhir.utils.safe_get`](#fyronfhirutilssafeget)

## `fyron.fhir.auth.Auth`

Simplified authentication wrapper for Fyron sessions.

**Import path:** `fyron.fhir.auth.Auth`

```python
Auth(self, auth_url: Optional[str] = None, auth_type: str = 'token', refresh_url: Optional[str] = None, username: Optional[str] = None, auth_method: str = 'env', token_auth_method: Optional[str] = None, token: Optional[str] = None, max_login_attempts: int = 3, token_refresh_delta: Optional[Union[int, timedelta]] = None, session: Optional[requests.Session] = None, *, client_id: Optional[str] = None, client_secret: Optional[str] = None, scope: Optional[str] = None, token_cache: Optional[str] = None, allow_reauthentication: bool = True, device_authorization_endpoint: Optional[str] = None, token_endpoint: Optional[str] = None, authorization_endpoint: Optional[str] = None, device_code_callback = None, client_auth_method: Optional[str] = None)
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `auth_url` | no | `Optional[str]` | `None` | See signature. |
| `auth_type` | no | `str` | `'token'` | See signature. |
| `refresh_url` | no | `Optional[str]` | `None` | See signature. |
| `username` | no | `Optional[str]` | `None` | See signature. |
| `auth_method` | no | `str` | `'env'` | See signature. |
| `token_auth_method` | no | `Optional[str]` | `None` | See signature. |
| `token` | no | `Optional[str]` | `None` | See signature. |
| `max_login_attempts` | no | `int` | `3` | See signature. |
| `token_refresh_delta` | no | `Optional[Union[int, timedelta]]` | `None` | See signature. |
| `session` | no | `Optional[requests.Session]` | `None` | See signature. |
| `client_id` | no | `Optional[str]` | `None` | See signature. |
| `client_secret` | no | `Optional[str]` | `None` | See signature. |
| `scope` | no | `Optional[str]` | `None` | See signature. |
| `token_cache` | no | `Optional[str]` | `None` | See signature. |
| `allow_reauthentication` | no | `bool` | `True` | See signature. |
| `device_authorization_endpoint` | no | `Optional[str]` | `None` | See signature. |
| `token_endpoint` | no | `Optional[str]` | `None` | See signature. |
| `authorization_endpoint` | no | `Optional[str]` | `None` | See signature. |
| `device_code_callback` | no |  | `None` | See signature. |
| `client_auth_method` | no | `Optional[str]` | `None` | See signature. |

### Returns

Class constructor.

**See also:** [FHIR module guide](../modules/fhir.md).

### Public Methods

#### `fyron.fhir.auth.Auth.client_credentials`

Create service-account OAuth auth, optionally using OIDC discovery.

**Import path:** `fyron.fhir.auth.Auth.client_credentials`

```python
Auth.client_credentials(cls, *, client_id: str, client_secret: str, auth_url: Optional[str] = None, token_endpoint: Optional[str] = None, scope: str = '', client_auth_method: Optional[str] = None, session: Optional[requests.Session] = None) -> 'Auth'
```

#### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `client_id` | yes | `str` |  | See signature. |
| `client_secret` | yes | `str` |  | See signature. |
| `auth_url` | no | `Optional[str]` | `None` | See signature. |
| `token_endpoint` | no | `Optional[str]` | `None` | See signature. |
| `scope` | no | `str` | `''` | See signature. |
| `client_auth_method` | no | `Optional[str]` | `None` | See signature. |
| `session` | no | `Optional[requests.Session]` | `None` | See signature. |

#### Returns

`'Auth'`

**See also:** [FHIR module guide](../modules/fhir.md).

#### `fyron.fhir.auth.Auth.token_env`

Create token-based auth using credentials from environment variables.

**Import path:** `fyron.fhir.auth.Auth.token_env`

```python
Auth.token_env(cls, *, auth_url: str, refresh_url: Optional[str] = None, token_auth_method: str = 'basic', token: Optional[str] = None, max_login_attempts: int = 3, token_refresh_delta: Optional[Union[int, timedelta]] = None, session: Optional[requests.Session] = None) -> 'Auth'
```

#### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `auth_url` | yes | `str` |  | See signature. |
| `refresh_url` | no | `Optional[str]` | `None` | See signature. |
| `token_auth_method` | no | `str` | `'basic'` | See signature. |
| `token` | no | `Optional[str]` | `None` | See signature. |
| `max_login_attempts` | no | `int` | `3` | See signature. |
| `token_refresh_delta` | no | `Optional[Union[int, timedelta]]` | `None` | See signature. |
| `session` | no | `Optional[requests.Session]` | `None` | See signature. |

#### Returns

`'Auth'`

**See also:** [FHIR module guide](../modules/fhir.md).

#### `fyron.fhir.auth.Auth.close`

Close the underlying session.

**Import path:** `fyron.fhir.auth.Auth.close`

```python
Auth.close(self) -> None
```

#### Parameters

No parameters documented.

#### Returns

`None`

**See also:** [FHIR module guide](../modules/fhir.md).

## `fyron.fhir.auth.TokenAuth`

Very small token auth helper.

**Import path:** `fyron.fhir.auth.TokenAuth`

```python
TokenAuth(self, username: str, password: str, auth_url: str, refresh_url: Optional[str] = None, token: Optional[str] = None, token_refresh_delta: Optional[Union[int, timedelta]] = None, max_login_attempts: int = 3, session: Optional[requests.Session] = None, token_field: str = 'access_token', auth_method: str = 'basic')
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `username` | yes | `str` |  | See signature. |
| `password` | yes | `str` |  | See signature. |
| `auth_url` | yes | `str` |  | See signature. |
| `refresh_url` | no | `Optional[str]` | `None` | See signature. |
| `token` | no | `Optional[str]` | `None` | See signature. |
| `token_refresh_delta` | no | `Optional[Union[int, timedelta]]` | `None` | See signature. |
| `max_login_attempts` | no | `int` | `3` | See signature. |
| `session` | no | `Optional[requests.Session]` | `None` | See signature. |
| `token_field` | no | `str` | `'access_token'` | See signature. |
| `auth_method` | no | `str` | `'basic'` | See signature. |

### Returns

Class constructor.

**See also:** [FHIR module guide](../modules/fhir.md).

### Public Methods

#### `fyron.fhir.auth.TokenAuth.is_refresh_required`

Return True if token should be refreshed.

**Import path:** `fyron.fhir.auth.TokenAuth.is_refresh_required`

```python
TokenAuth.is_refresh_required(self) -> bool
```

#### Parameters

No parameters documented.

#### Returns

`bool`

**See also:** [FHIR module guide](../modules/fhir.md).

## `fyron.fhir.auth.now_utc`

Return current UTC datetime.

**Import path:** `fyron.fhir.auth.now_utc`

```python
now_utc() -> datetime
```

### Parameters

No parameters documented.

### Returns

`datetime`

**See also:** [FHIR module guide](../modules/fhir.md).

## `fyron.fhir.builder.attachment`

Build a FHIR Attachment.

**Import path:** `fyron.fhir.builder.attachment`

```python
attachment(url: str | None = None, *, content_type: str | None = None, title: str | None = None, data: str | None = None, creation: str | None = None) -> dict[str, Any]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `url` | no | `str  or  None` | `None` | See signature. |
| `content_type` | no | `str  or  None` | `None` | See signature. |
| `title` | no | `str  or  None` | `None` | See signature. |
| `data` | no | `str  or  None` | `None` | See signature. |
| `creation` | no | `str  or  None` | `None` | See signature. |

### Returns

`dict[str, Any]`

**See also:** [FHIR module guide](../modules/fhir.md).

## `fyron.fhir.builder.build_bundle`

Build a collection or transaction FHIR Bundle.

**Import path:** `fyron.fhir.builder.build_bundle`

```python
build_bundle(resources: Sequence[dict[str, Any]], *, bundle_type: str, bundle_id: str | None = None, transaction_method: str = 'POST', if_none_exist: str | dict[str, str] | None = None, version: str = FHIR_R4) -> dict[str, Any]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `resources` | yes | `Sequence[dict[str, Any]]` |  | See signature. |
| `bundle_type` | yes | `str` |  | See signature. |
| `bundle_id` | no | `str  or  None` | `None` | See signature. |
| `transaction_method` | no | `str` | `'POST'` | See signature. |
| `if_none_exist` | no | `str  or  dict[str, str]  or  None` | `None` | See signature. |
| `version` | no | `str` | `FHIR_R4` | See signature. |

### Returns

`dict[str, Any]`

**See also:** [FHIR module guide](../modules/fhir.md).

## `fyron.fhir.builder.build_condition`

Build a FHIR Condition with optional evidence links.

**Import path:** `fyron.fhir.builder.build_condition`

```python
build_condition(*, subject: str | dict[str, Any], code: dict[str, Any] | str, condition_id: str | None = None, clinical_status: dict[str, Any] | str | None = None, verification_status: dict[str, Any] | str | None = None, onset: str | None = None, recorded_date: str | None = None, evidence: Sequence[str | dict[str, Any]] | None = None, profile: str | Sequence[str] | None = None, identifier: dict[str, Any] | Sequence[dict[str, Any]] | None = None, meta_source: str | None = None, tag: dict[str, Any] | Sequence[dict[str, Any]] | None = None, security: dict[str, Any] | Sequence[dict[str, Any]] | None = None, extension: dict[str, Any] | Sequence[dict[str, Any]] | None = None, version: str = FHIR_R4) -> dict[str, Any]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `subject` | yes | `str  or  dict[str, Any]` |  | See signature. |
| `code` | yes | `dict[str, Any]  or  str` |  | See signature. |
| `condition_id` | no | `str  or  None` | `None` | See signature. |
| `clinical_status` | no | `dict[str, Any]  or  str  or  None` | `None` | See signature. |
| `verification_status` | no | `dict[str, Any]  or  str  or  None` | `None` | See signature. |
| `onset` | no | `str  or  None` | `None` | See signature. |
| `recorded_date` | no | `str  or  None` | `None` | See signature. |
| `evidence` | no | `Sequence[str  or  dict[str, Any]]  or  None` | `None` | See signature. |
| `profile` | no | `str  or  Sequence[str]  or  None` | `None` | See signature. |
| `identifier` | no | `dict[str, Any]  or  Sequence[dict[str, Any]]  or  None` | `None` | See signature. |
| `meta_source` | no | `str  or  None` | `None` | See signature. |
| `tag` | no | `dict[str, Any]  or  Sequence[dict[str, Any]]  or  None` | `None` | See signature. |
| `security` | no | `dict[str, Any]  or  Sequence[dict[str, Any]]  or  None` | `None` | See signature. |
| `extension` | no | `dict[str, Any]  or  Sequence[dict[str, Any]]  or  None` | `None` | See signature. |
| `version` | no | `str` | `FHIR_R4` | See signature. |

### Returns

`dict[str, Any]`

**See also:** [FHIR module guide](../modules/fhir.md).

## `fyron.fhir.builder.build_diagnostic_report`

Build a FHIR DiagnosticReport that groups observations or summaries.

**Import path:** `fyron.fhir.builder.build_diagnostic_report`

```python
build_diagnostic_report(*, subject: str | dict[str, Any], code: dict[str, Any] | str, results: Sequence[str | dict[str, Any]] | None = None, report_id: str | None = None, status: str = 'final', effective: str | None = None, issued: str | None = None, imaging_study: Sequence[str | dict[str, Any]] | None = None, conclusion: str | None = None, presented_form: Sequence[dict[str, Any]] | None = None, profile: str | Sequence[str] | None = None, identifier: dict[str, Any] | Sequence[dict[str, Any]] | None = None, meta_source: str | None = None, tag: dict[str, Any] | Sequence[dict[str, Any]] | None = None, security: dict[str, Any] | Sequence[dict[str, Any]] | None = None, extension: dict[str, Any] | Sequence[dict[str, Any]] | None = None, version: str = FHIR_R4) -> dict[str, Any]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `subject` | yes | `str  or  dict[str, Any]` |  | See signature. |
| `code` | yes | `dict[str, Any]  or  str` |  | See signature. |
| `results` | no | `Sequence[str  or  dict[str, Any]]  or  None` | `None` | See signature. |
| `report_id` | no | `str  or  None` | `None` | See signature. |
| `status` | no | `str` | `'final'` | See signature. |
| `effective` | no | `str  or  None` | `None` | See signature. |
| `issued` | no | `str  or  None` | `None` | See signature. |
| `imaging_study` | no | `Sequence[str  or  dict[str, Any]]  or  None` | `None` | See signature. |
| `conclusion` | no | `str  or  None` | `None` | See signature. |
| `presented_form` | no | `Sequence[dict[str, Any]]  or  None` | `None` | See signature. |
| `profile` | no | `str  or  Sequence[str]  or  None` | `None` | See signature. |
| `identifier` | no | `dict[str, Any]  or  Sequence[dict[str, Any]]  or  None` | `None` | See signature. |
| `meta_source` | no | `str  or  None` | `None` | See signature. |
| `tag` | no | `dict[str, Any]  or  Sequence[dict[str, Any]]  or  None` | `None` | See signature. |
| `security` | no | `dict[str, Any]  or  Sequence[dict[str, Any]]  or  None` | `None` | See signature. |
| `extension` | no | `dict[str, Any]  or  Sequence[dict[str, Any]]  or  None` | `None` | See signature. |
| `version` | no | `str` | `FHIR_R4` | See signature. |

### Returns

`dict[str, Any]`

**See also:** [FHIR module guide](../modules/fhir.md).

## `fyron.fhir.builder.build_document_reference`

Build a FHIR DocumentReference for source reports or generated summaries.

**Import path:** `fyron.fhir.builder.build_document_reference`

```python
build_document_reference(*, subject: str | dict[str, Any], url: str | None = None, title: str | None = None, content_type: str | None = None, document_id: str | None = None, status: str = 'current', doc_status: str | None = None, type_code: dict[str, Any] | str | None = None, date: str | None = None, description: str | None = None, profile: str | Sequence[str] | None = None, identifier: dict[str, Any] | Sequence[dict[str, Any]] | None = None, meta_source: str | None = None, tag: dict[str, Any] | Sequence[dict[str, Any]] | None = None, security: dict[str, Any] | Sequence[dict[str, Any]] | None = None, extension: dict[str, Any] | Sequence[dict[str, Any]] | None = None, version: str = FHIR_R4) -> dict[str, Any]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `subject` | yes | `str  or  dict[str, Any]` |  | See signature. |
| `url` | no | `str  or  None` | `None` | See signature. |
| `title` | no | `str  or  None` | `None` | See signature. |
| `content_type` | no | `str  or  None` | `None` | See signature. |
| `document_id` | no | `str  or  None` | `None` | See signature. |
| `status` | no | `str` | `'current'` | See signature. |
| `doc_status` | no | `str  or  None` | `None` | See signature. |
| `type_code` | no | `dict[str, Any]  or  str  or  None` | `None` | See signature. |
| `date` | no | `str  or  None` | `None` | See signature. |
| `description` | no | `str  or  None` | `None` | See signature. |
| `profile` | no | `str  or  Sequence[str]  or  None` | `None` | See signature. |
| `identifier` | no | `dict[str, Any]  or  Sequence[dict[str, Any]]  or  None` | `None` | See signature. |
| `meta_source` | no | `str  or  None` | `None` | See signature. |
| `tag` | no | `dict[str, Any]  or  Sequence[dict[str, Any]]  or  None` | `None` | See signature. |
| `security` | no | `dict[str, Any]  or  Sequence[dict[str, Any]]  or  None` | `None` | See signature. |
| `extension` | no | `dict[str, Any]  or  Sequence[dict[str, Any]]  or  None` | `None` | See signature. |
| `version` | no | `str` | `FHIR_R4` | See signature. |

### Returns

`dict[str, Any]`

**See also:** [FHIR module guide](../modules/fhir.md).

## `fyron.fhir.builder.build_encounter`

Build a minimal FHIR Encounter resource.

**Import path:** `fyron.fhir.builder.build_encounter`

```python
build_encounter(*, subject: str | dict[str, Any], status: str = 'finished', encounter_class: dict[str, Any] | str | None = None, encounter_id: str | None = None, period_start: str | None = None, period_end: str | None = None, reason_code: dict[str, Any] | str | None = None, profile: str | Sequence[str] | None = None, identifier: dict[str, Any] | Sequence[dict[str, Any]] | None = None, version: str = FHIR_R4) -> dict[str, Any]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `subject` | yes | `str  or  dict[str, Any]` |  | See signature. |
| `status` | no | `str` | `'finished'` | See signature. |
| `encounter_class` | no | `dict[str, Any]  or  str  or  None` | `None` | See signature. |
| `encounter_id` | no | `str  or  None` | `None` | See signature. |
| `period_start` | no | `str  or  None` | `None` | See signature. |
| `period_end` | no | `str  or  None` | `None` | See signature. |
| `reason_code` | no | `dict[str, Any]  or  str  or  None` | `None` | See signature. |
| `profile` | no | `str  or  Sequence[str]  or  None` | `None` | See signature. |
| `identifier` | no | `dict[str, Any]  or  Sequence[dict[str, Any]]  or  None` | `None` | See signature. |
| `version` | no | `str` | `FHIR_R4` | See signature. |

### Returns

`dict[str, Any]`

**See also:** [FHIR module guide](../modules/fhir.md).

## `fyron.fhir.builder.build_endpoint`

Build a FHIR Endpoint resource for a model or FHIR API endpoint.

**Import path:** `fyron.fhir.builder.build_endpoint`

```python
build_endpoint(*, address: str, endpoint_id: str | None = None, name: str | None = None, status: str = 'active', connection_type_code: str = 'hl7-fhir-rest', profile: str | Sequence[str] | None = None, identifier: dict[str, Any] | Sequence[dict[str, Any]] | None = None, meta_source: str | None = None, tag: dict[str, Any] | Sequence[dict[str, Any]] | None = None, security: dict[str, Any] | Sequence[dict[str, Any]] | None = None, extension: dict[str, Any] | Sequence[dict[str, Any]] | None = None, version: str = FHIR_R4) -> dict[str, Any]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `address` | yes | `str` |  | See signature. |
| `endpoint_id` | no | `str  or  None` | `None` | See signature. |
| `name` | no | `str  or  None` | `None` | See signature. |
| `status` | no | `str` | `'active'` | See signature. |
| `connection_type_code` | no | `str` | `'hl7-fhir-rest'` | See signature. |
| `profile` | no | `str  or  Sequence[str]  or  None` | `None` | See signature. |
| `identifier` | no | `dict[str, Any]  or  Sequence[dict[str, Any]]  or  None` | `None` | See signature. |
| `meta_source` | no | `str  or  None` | `None` | See signature. |
| `tag` | no | `dict[str, Any]  or  Sequence[dict[str, Any]]  or  None` | `None` | See signature. |
| `security` | no | `dict[str, Any]  or  Sequence[dict[str, Any]]  or  None` | `None` | See signature. |
| `extension` | no | `dict[str, Any]  or  Sequence[dict[str, Any]]  or  None` | `None` | See signature. |
| `version` | no | `str` | `FHIR_R4` | See signature. |

### Returns

`dict[str, Any]`

**See also:** [FHIR module guide](../modules/fhir.md).

## `fyron.fhir.builder.build_imaging_measurement_bundle`

Build a FHIR bundle for imaging-derived quantitative measurements.

**Import path:** `fyron.fhir.builder.build_imaging_measurement_bundle`

```python
build_imaging_measurement_bundle(*, subject: str | dict[str, Any], study_instance_uid: str, measurements: Sequence[dict[str, Any]], series_instance_uid: str | None = None, series_description: str | None = None, model_name: str | None = None, model_endpoint_url: str | None = None, id_prefix: str | None = None, bundle_type: str, version: str = FHIR_R4) -> dict[str, Any]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `subject` | yes | `str  or  dict[str, Any]` |  | See signature. |
| `study_instance_uid` | yes | `str` |  | See signature. |
| `measurements` | yes | `Sequence[dict[str, Any]]` |  | See signature. |
| `series_instance_uid` | no | `str  or  None` | `None` | See signature. |
| `series_description` | no | `str  or  None` | `None` | See signature. |
| `model_name` | no | `str  or  None` | `None` | See signature. |
| `model_endpoint_url` | no | `str  or  None` | `None` | See signature. |
| `id_prefix` | no | `str  or  None` | `None` | See signature. |
| `bundle_type` | yes | `str` |  | See signature. |
| `version` | no | `str` | `FHIR_R4` | See signature. |

### Returns

`dict[str, Any]`

**See also:** [FHIR module guide](../modules/fhir.md).

## `fyron.fhir.builder.build_imaging_study_reference`

Build a minimal FHIR ImagingStudy resource with optional series context.

**Import path:** `fyron.fhir.builder.build_imaging_study_reference`

```python
build_imaging_study_reference(*, subject: str | dict[str, Any], study_instance_uid: str, imaging_study_id: str | None = None, series_instance_uid: str | None = None, series_description: str | None = None, modality_code: str | None = None, started: str | None = None, profile: str | Sequence[str] | None = None, meta_source: str | None = None, tag: dict[str, Any] | Sequence[dict[str, Any]] | None = None, security: dict[str, Any] | Sequence[dict[str, Any]] | None = None, extension: dict[str, Any] | Sequence[dict[str, Any]] | None = None, version: str = FHIR_R4) -> dict[str, Any]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `subject` | yes | `str  or  dict[str, Any]` |  | See signature. |
| `study_instance_uid` | yes | `str` |  | See signature. |
| `imaging_study_id` | no | `str  or  None` | `None` | See signature. |
| `series_instance_uid` | no | `str  or  None` | `None` | See signature. |
| `series_description` | no | `str  or  None` | `None` | See signature. |
| `modality_code` | no | `str  or  None` | `None` | See signature. |
| `started` | no | `str  or  None` | `None` | See signature. |
| `profile` | no | `str  or  Sequence[str]  or  None` | `None` | See signature. |
| `meta_source` | no | `str  or  None` | `None` | See signature. |
| `tag` | no | `dict[str, Any]  or  Sequence[dict[str, Any]]  or  None` | `None` | See signature. |
| `security` | no | `dict[str, Any]  or  Sequence[dict[str, Any]]  or  None` | `None` | See signature. |
| `extension` | no | `dict[str, Any]  or  Sequence[dict[str, Any]]  or  None` | `None` | See signature. |
| `version` | no | `str` | `FHIR_R4` | See signature. |

### Returns

`dict[str, Any]`

**See also:** [FHIR module guide](../modules/fhir.md).

## `fyron.fhir.builder.build_llm_extraction_bundle`

Build a FHIR bundle for LLM-extracted report evidence.

**Import path:** `fyron.fhir.builder.build_llm_extraction_bundle`

```python
build_llm_extraction_bundle(*, subject: str | dict[str, Any], source_report_url: str, observations: Sequence[dict[str, Any]] | None = None, conditions: Sequence[dict[str, Any]] | None = None, summary_text: str | None = None, model_name: str, model_endpoint_url: str | None = None, model_version: str | None = None, prompt_version: str | None = None, id_prefix: str | None = None, bundle_type: str, version: str = FHIR_R4) -> dict[str, Any]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `subject` | yes | `str  or  dict[str, Any]` |  | See signature. |
| `source_report_url` | yes | `str` |  | See signature. |
| `observations` | no | `Sequence[dict[str, Any]]  or  None` | `None` | See signature. |
| `conditions` | no | `Sequence[dict[str, Any]]  or  None` | `None` | See signature. |
| `summary_text` | no | `str  or  None` | `None` | See signature. |
| `model_name` | yes | `str` |  | See signature. |
| `model_endpoint_url` | no | `str  or  None` | `None` | See signature. |
| `model_version` | no | `str  or  None` | `None` | See signature. |
| `prompt_version` | no | `str  or  None` | `None` | See signature. |
| `id_prefix` | no | `str  or  None` | `None` | See signature. |
| `bundle_type` | yes | `str` |  | See signature. |
| `version` | no | `str` | `FHIR_R4` | See signature. |

### Returns

`dict[str, Any]`

**See also:** [FHIR module guide](../modules/fhir.md).

## `fyron.fhir.builder.build_medication_statement`

Build a minimal FHIR MedicationStatement resource.

**Import path:** `fyron.fhir.builder.build_medication_statement`

```python
build_medication_statement(*, subject: str | dict[str, Any], medication: dict[str, Any] | str, medication_statement_id: str | None = None, status: str = 'active', effective: str | None = None, date_asserted: str | None = None, reason_code: dict[str, Any] | str | None = None, profile: str | Sequence[str] | None = None, identifier: dict[str, Any] | Sequence[dict[str, Any]] | None = None, version: str = FHIR_R4) -> dict[str, Any]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `subject` | yes | `str  or  dict[str, Any]` |  | See signature. |
| `medication` | yes | `dict[str, Any]  or  str` |  | See signature. |
| `medication_statement_id` | no | `str  or  None` | `None` | See signature. |
| `status` | no | `str` | `'active'` | See signature. |
| `effective` | no | `str  or  None` | `None` | See signature. |
| `date_asserted` | no | `str  or  None` | `None` | See signature. |
| `reason_code` | no | `dict[str, Any]  or  str  or  None` | `None` | See signature. |
| `profile` | no | `str  or  Sequence[str]  or  None` | `None` | See signature. |
| `identifier` | no | `dict[str, Any]  or  Sequence[dict[str, Any]]  or  None` | `None` | See signature. |
| `version` | no | `str` | `FHIR_R4` | See signature. |

### Returns

`dict[str, Any]`

**See also:** [FHIR module guide](../modules/fhir.md).

## `fyron.fhir.builder.build_model_device`

Build a FHIR Device resource for an AI/model system.

**Import path:** `fyron.fhir.builder.build_model_device`

```python
build_model_device(*, model_name: str, model_version: str | None = None, device_id: str | None = None, manufacturer: str = 'Bits & Flames', endpoint: str | dict[str, Any] | None = None, profile: str | Sequence[str] | None = None, identifier: dict[str, Any] | Sequence[dict[str, Any]] | None = None, meta_source: str | None = None, tag: dict[str, Any] | Sequence[dict[str, Any]] | None = None, security: dict[str, Any] | Sequence[dict[str, Any]] | None = None, extension: dict[str, Any] | Sequence[dict[str, Any]] | None = None, version: str = FHIR_R4) -> dict[str, Any]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `model_name` | yes | `str` |  | See signature. |
| `model_version` | no | `str  or  None` | `None` | See signature. |
| `device_id` | no | `str  or  None` | `None` | See signature. |
| `manufacturer` | no | `str` | `'Bits & Flames'` | See signature. |
| `endpoint` | no | `str  or  dict[str, Any]  or  None` | `None` | See signature. |
| `profile` | no | `str  or  Sequence[str]  or  None` | `None` | See signature. |
| `identifier` | no | `dict[str, Any]  or  Sequence[dict[str, Any]]  or  None` | `None` | See signature. |
| `meta_source` | no | `str  or  None` | `None` | See signature. |
| `tag` | no | `dict[str, Any]  or  Sequence[dict[str, Any]]  or  None` | `None` | See signature. |
| `security` | no | `dict[str, Any]  or  Sequence[dict[str, Any]]  or  None` | `None` | See signature. |
| `extension` | no | `dict[str, Any]  or  Sequence[dict[str, Any]]  or  None` | `None` | See signature. |
| `version` | no | `str` | `FHIR_R4` | See signature. |

### Returns

`dict[str, Any]`

**See also:** [FHIR module guide](../modules/fhir.md).

## `fyron.fhir.builder.build_observation`

Build a FHIR Observation for extracted or measured values.

**Import path:** `fyron.fhir.builder.build_observation`

```python
build_observation(*, subject: str | dict[str, Any], code: dict[str, Any] | str, value: Any | None = None, status: str = 'final', observation_id: str | None = None, effective: str | None = None, issued: str | None = None, category: dict[str, Any] | Sequence[dict[str, Any]] | None = None, unit: str | None = None, value_type: str = 'quantity', derived_from: Sequence[str | dict[str, Any]] | None = None, method: dict[str, Any] | str | None = None, body_site: dict[str, Any] | str | None = None, imaging_series_uid: str | None = None, components: Sequence[dict[str, Any]] | None = None, data_absent_reason: dict[str, Any] | str | None = None, performer: Sequence[str | dict[str, Any]] | None = None, encounter: str | dict[str, Any] | None = None, interpretation: dict[str, Any] | str | Sequence[dict[str, Any] | str] | None = None, note: str | Sequence[str] | None = None, profile: str | Sequence[str] | None = None, identifier: dict[str, Any] | Sequence[dict[str, Any]] | None = None, meta_source: str | None = None, tag: dict[str, Any] | Sequence[dict[str, Any]] | None = None, security: dict[str, Any] | Sequence[dict[str, Any]] | None = None, extension: dict[str, Any] | Sequence[dict[str, Any]] | None = None, version: str = FHIR_R4) -> dict[str, Any]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `subject` | yes | `str  or  dict[str, Any]` |  | See signature. |
| `code` | yes | `dict[str, Any]  or  str` |  | See signature. |
| `value` | no | `Any  or  None` | `None` | See signature. |
| `status` | no | `str` | `'final'` | See signature. |
| `observation_id` | no | `str  or  None` | `None` | See signature. |
| `effective` | no | `str  or  None` | `None` | See signature. |
| `issued` | no | `str  or  None` | `None` | See signature. |
| `category` | no | `dict[str, Any]  or  Sequence[dict[str, Any]]  or  None` | `None` | See signature. |
| `unit` | no | `str  or  None` | `None` | See signature. |
| `value_type` | no | `str` | `'quantity'` | See signature. |
| `derived_from` | no | `Sequence[str  or  dict[str, Any]]  or  None` | `None` | See signature. |
| `method` | no | `dict[str, Any]  or  str  or  None` | `None` | See signature. |
| `body_site` | no | `dict[str, Any]  or  str  or  None` | `None` | See signature. |
| `imaging_series_uid` | no | `str  or  None` | `None` | See signature. |
| `components` | no | `Sequence[dict[str, Any]]  or  None` | `None` | See signature. |
| `data_absent_reason` | no | `dict[str, Any]  or  str  or  None` | `None` | See signature. |
| `performer` | no | `Sequence[str  or  dict[str, Any]]  or  None` | `None` | See signature. |
| `encounter` | no | `str  or  dict[str, Any]  or  None` | `None` | See signature. |
| `interpretation` | no | `dict[str, Any]  or  str  or  Sequence[dict[str, Any]  or  str]  or  None` | `None` | See signature. |
| `note` | no | `str  or  Sequence[str]  or  None` | `None` | See signature. |
| `profile` | no | `str  or  Sequence[str]  or  None` | `None` | See signature. |
| `identifier` | no | `dict[str, Any]  or  Sequence[dict[str, Any]]  or  None` | `None` | See signature. |
| `meta_source` | no | `str  or  None` | `None` | See signature. |
| `tag` | no | `dict[str, Any]  or  Sequence[dict[str, Any]]  or  None` | `None` | See signature. |
| `security` | no | `dict[str, Any]  or  Sequence[dict[str, Any]]  or  None` | `None` | See signature. |
| `extension` | no | `dict[str, Any]  or  Sequence[dict[str, Any]]  or  None` | `None` | See signature. |
| `version` | no | `str` | `FHIR_R4` | See signature. |

### Returns

`dict[str, Any]`

**See also:** [FHIR module guide](../modules/fhir.md).

## `fyron.fhir.builder.build_observation_component`

Build a FHIR Observation.component item.

**Import path:** `fyron.fhir.builder.build_observation_component`

```python
build_observation_component(*, code: dict[str, Any] | str, value: Any | None = None, unit: str | None = None, value_type: str = 'quantity', data_absent_reason: dict[str, Any] | str | None = None, interpretation: dict[str, Any] | str | None = None) -> dict[str, Any]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `code` | yes | `dict[str, Any]  or  str` |  | See signature. |
| `value` | no | `Any  or  None` | `None` | See signature. |
| `unit` | no | `str  or  None` | `None` | See signature. |
| `value_type` | no | `str` | `'quantity'` | See signature. |
| `data_absent_reason` | no | `dict[str, Any]  or  str  or  None` | `None` | See signature. |
| `interpretation` | no | `dict[str, Any]  or  str  or  None` | `None` | See signature. |

### Returns

`dict[str, Any]`

**See also:** [FHIR module guide](../modules/fhir.md).

## `fyron.fhir.builder.build_procedure`

Build a minimal FHIR Procedure resource.

**Import path:** `fyron.fhir.builder.build_procedure`

```python
build_procedure(*, subject: str | dict[str, Any], code: dict[str, Any] | str, procedure_id: str | None = None, status: str = 'completed', performed: str | None = None, encounter: str | dict[str, Any] | None = None, reason_code: dict[str, Any] | str | None = None, body_site: dict[str, Any] | str | None = None, profile: str | Sequence[str] | None = None, identifier: dict[str, Any] | Sequence[dict[str, Any]] | None = None, version: str = FHIR_R4) -> dict[str, Any]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `subject` | yes | `str  or  dict[str, Any]` |  | See signature. |
| `code` | yes | `dict[str, Any]  or  str` |  | See signature. |
| `procedure_id` | no | `str  or  None` | `None` | See signature. |
| `status` | no | `str` | `'completed'` | See signature. |
| `performed` | no | `str  or  None` | `None` | See signature. |
| `encounter` | no | `str  or  dict[str, Any]  or  None` | `None` | See signature. |
| `reason_code` | no | `dict[str, Any]  or  str  or  None` | `None` | See signature. |
| `body_site` | no | `dict[str, Any]  or  str  or  None` | `None` | See signature. |
| `profile` | no | `str  or  Sequence[str]  or  None` | `None` | See signature. |
| `identifier` | no | `dict[str, Any]  or  Sequence[dict[str, Any]]  or  None` | `None` | See signature. |
| `version` | no | `str` | `FHIR_R4` | See signature. |

### Returns

`dict[str, Any]`

**See also:** [FHIR module guide](../modules/fhir.md).

## `fyron.fhir.builder.build_provenance`

Build a FHIR Provenance resource linking generated outputs to evidence.

**Import path:** `fyron.fhir.builder.build_provenance`

```python
build_provenance(*, targets: Sequence[str | dict[str, Any]], agent: str | dict[str, Any] | None = None, entity: Sequence[str | dict[str, Any]] | None = None, provenance_id: str | None = None, recorded: str | None = None, activity: dict[str, Any] | str | None = None, prompt_version: str | None = None, profile: str | Sequence[str] | None = None, meta_source: str | None = None, tag: dict[str, Any] | Sequence[dict[str, Any]] | None = None, security: dict[str, Any] | Sequence[dict[str, Any]] | None = None, extension: dict[str, Any] | Sequence[dict[str, Any]] | None = None, version: str = FHIR_R4) -> dict[str, Any]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `targets` | yes | `Sequence[str  or  dict[str, Any]]` |  | See signature. |
| `agent` | no | `str  or  dict[str, Any]  or  None` | `None` | See signature. |
| `entity` | no | `Sequence[str  or  dict[str, Any]]  or  None` | `None` | See signature. |
| `provenance_id` | no | `str  or  None` | `None` | See signature. |
| `recorded` | no | `str  or  None` | `None` | See signature. |
| `activity` | no | `dict[str, Any]  or  str  or  None` | `None` | See signature. |
| `prompt_version` | no | `str  or  None` | `None` | See signature. |
| `profile` | no | `str  or  Sequence[str]  or  None` | `None` | See signature. |
| `meta_source` | no | `str  or  None` | `None` | See signature. |
| `tag` | no | `dict[str, Any]  or  Sequence[dict[str, Any]]  or  None` | `None` | See signature. |
| `security` | no | `dict[str, Any]  or  Sequence[dict[str, Any]]  or  None` | `None` | See signature. |
| `extension` | no | `dict[str, Any]  or  Sequence[dict[str, Any]]  or  None` | `None` | See signature. |
| `version` | no | `str` | `FHIR_R4` | See signature. |

### Returns

`dict[str, Any]`

**See also:** [FHIR module guide](../modules/fhir.md).

## `fyron.fhir.builder.build_service_request`

Build a minimal FHIR ServiceRequest resource.

**Import path:** `fyron.fhir.builder.build_service_request`

```python
build_service_request(*, subject: str | dict[str, Any], code: dict[str, Any] | str, service_request_id: str | None = None, status: str = 'active', intent: str = 'order', authored_on: str | None = None, requester: str | dict[str, Any] | None = None, reason_code: dict[str, Any] | str | None = None, profile: str | Sequence[str] | None = None, identifier: dict[str, Any] | Sequence[dict[str, Any]] | None = None, version: str = FHIR_R4) -> dict[str, Any]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `subject` | yes | `str  or  dict[str, Any]` |  | See signature. |
| `code` | yes | `dict[str, Any]  or  str` |  | See signature. |
| `service_request_id` | no | `str  or  None` | `None` | See signature. |
| `status` | no | `str` | `'active'` | See signature. |
| `intent` | no | `str` | `'order'` | See signature. |
| `authored_on` | no | `str  or  None` | `None` | See signature. |
| `requester` | no | `str  or  dict[str, Any]  or  None` | `None` | See signature. |
| `reason_code` | no | `dict[str, Any]  or  str  or  None` | `None` | See signature. |
| `profile` | no | `str  or  Sequence[str]  or  None` | `None` | See signature. |
| `identifier` | no | `dict[str, Any]  or  Sequence[dict[str, Any]]  or  None` | `None` | See signature. |
| `version` | no | `str` | `FHIR_R4` | See signature. |

### Returns

`dict[str, Any]`

**See also:** [FHIR module guide](../modules/fhir.md).

## `fyron.fhir.builder.build_specimen`

Build a minimal FHIR Specimen resource.

**Import path:** `fyron.fhir.builder.build_specimen`

```python
build_specimen(*, subject: str | dict[str, Any], specimen_type: dict[str, Any] | str | None = None, specimen_id: str | None = None, status: str = 'available', received_time: str | None = None, collection_time: str | None = None, profile: str | Sequence[str] | None = None, identifier: dict[str, Any] | Sequence[dict[str, Any]] | None = None, version: str = FHIR_R4) -> dict[str, Any]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `subject` | yes | `str  or  dict[str, Any]` |  | See signature. |
| `specimen_type` | no | `dict[str, Any]  or  str  or  None` | `None` | See signature. |
| `specimen_id` | no | `str  or  None` | `None` | See signature. |
| `status` | no | `str` | `'available'` | See signature. |
| `received_time` | no | `str  or  None` | `None` | See signature. |
| `collection_time` | no | `str  or  None` | `None` | See signature. |
| `profile` | no | `str  or  Sequence[str]  or  None` | `None` | See signature. |
| `identifier` | no | `dict[str, Any]  or  Sequence[dict[str, Any]]  or  None` | `None` | See signature. |
| `version` | no | `str` | `FHIR_R4` | See signature. |

### Returns

`dict[str, Any]`

**See also:** [FHIR module guide](../modules/fhir.md).

## `fyron.fhir.builder.codeable_concept`

Build a FHIR CodeableConcept.

**Import path:** `fyron.fhir.builder.codeable_concept`

```python
codeable_concept(code: str | None = None, *, system: str | None = None, display: str | None = None, text: str | None = None, codings: Sequence[dict[str, Any]] | None = None) -> dict[str, Any]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `code` | no | `str  or  None` | `None` | See signature. |
| `system` | no | `str  or  None` | `None` | See signature. |
| `display` | no | `str  or  None` | `None` | See signature. |
| `text` | no | `str  or  None` | `None` | See signature. |
| `codings` | no | `Sequence[dict[str, Any]]  or  None` | `None` | See signature. |

### Returns

`dict[str, Any]`

**See also:** [FHIR module guide](../modules/fhir.md).

## `fyron.fhir.builder.coding`

Build a FHIR Coding.

**Import path:** `fyron.fhir.builder.coding`

```python
coding(code: str, system: str | None = None, display: str | None = None) -> dict[str, Any]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `code` | yes | `str` |  | See signature. |
| `system` | no | `str  or  None` | `None` | See signature. |
| `display` | no | `str  or  None` | `None` | See signature. |

### Returns

`dict[str, Any]`

**See also:** [FHIR module guide](../modules/fhir.md).

## `fyron.fhir.builder.dicom_code`

Build a DICOM ontology Coding.

**Import path:** `fyron.fhir.builder.dicom_code`

```python
dicom_code(code: str, display: str | None = None) -> dict[str, Any]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `code` | yes | `str` |  | See signature. |
| `display` | no | `str  or  None` | `None` | See signature. |

### Returns

`dict[str, Any]`

**See also:** [FHIR module guide](../modules/fhir.md).

## `fyron.fhir.builder.icd10`

Build an ICD-10 Coding.

**Import path:** `fyron.fhir.builder.icd10`

```python
icd10(code: str, display: str | None = None) -> dict[str, Any]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `code` | yes | `str` |  | See signature. |
| `display` | no | `str  or  None` | `None` | See signature. |

### Returns

`dict[str, Any]`

**See also:** [FHIR module guide](../modules/fhir.md).

## `fyron.fhir.builder.identifier`

Build a FHIR Identifier.

**Import path:** `fyron.fhir.builder.identifier`

```python
identifier(value: str, system: str | None = None, use: str | None = None) -> dict[str, Any]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `value` | yes | `str` |  | See signature. |
| `system` | no | `str  or  None` | `None` | See signature. |
| `use` | no | `str  or  None` | `None` | See signature. |

### Returns

`dict[str, Any]`

**See also:** [FHIR module guide](../modules/fhir.md).

## `fyron.fhir.builder.loinc`

Build a LOINC Coding.

**Import path:** `fyron.fhir.builder.loinc`

```python
loinc(code: str, display: str | None = None) -> dict[str, Any]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `code` | yes | `str` |  | See signature. |
| `display` | no | `str  or  None` | `None` | See signature. |

### Returns

`dict[str, Any]`

**See also:** [FHIR module guide](../modules/fhir.md).

## `fyron.fhir.builder.quantity`

Build a FHIR Quantity.

**Import path:** `fyron.fhir.builder.quantity`

```python
quantity(value: int | float, unit: str | None = None, *, system: str = 'http://unitsofmeasure.org', code: str | None = None) -> dict[str, Any]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `value` | yes | `int  or  float` |  | See signature. |
| `unit` | no | `str  or  None` | `None` | See signature. |
| `system` | no | `str` | `'http://unitsofmeasure.org'` | See signature. |
| `code` | no | `str  or  None` | `None` | See signature. |

### Returns

`dict[str, Any]`

**See also:** [FHIR module guide](../modules/fhir.md).

## `fyron.fhir.builder.read_fhir_json`

Read a FHIR JSON payload from disk.

**Import path:** `fyron.fhir.builder.read_fhir_json`

```python
read_fhir_json(path: StrPath) -> dict[str, Any]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `path` | yes | `StrPath` |  | See signature. |

### Returns

`dict[str, Any]`

**See also:** [FHIR module guide](../modules/fhir.md).

## `fyron.fhir.builder.reference`

Build a FHIR Reference.

**Import path:** `fyron.fhir.builder.reference`

```python
reference(target: str | dict[str, Any], display: str | None = None) -> dict[str, Any]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `target` | yes | `str  or  dict[str, Any]` |  | See signature. |
| `display` | no | `str  or  None` | `None` | See signature. |

### Returns

`dict[str, Any]`

**See also:** [FHIR module guide](../modules/fhir.md).

## `fyron.fhir.builder.snomed`

Build a SNOMED CT Coding.

**Import path:** `fyron.fhir.builder.snomed`

```python
snomed(code: str, display: str | None = None) -> dict[str, Any]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `code` | yes | `str` |  | See signature. |
| `display` | no | `str  or  None` | `None` | See signature. |

### Returns

`dict[str, Any]`

**See also:** [FHIR module guide](../modules/fhir.md).

## `fyron.fhir.builder.summarize_fhir_bundle`

Return bundle counts, request methods, and local-reference status.

**Import path:** `fyron.fhir.builder.summarize_fhir_bundle`

```python
summarize_fhir_bundle(bundle: dict[str, Any]) -> dict[str, Any]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `bundle` | yes | `dict[str, Any]` |  | See signature. |

### Returns

`dict[str, Any]`

**See also:** [FHIR module guide](../modules/fhir.md).

## `fyron.fhir.builder.summarize_fhir_resource`

Return a compact, inspectable summary for one FHIR resource.

**Import path:** `fyron.fhir.builder.summarize_fhir_resource`

```python
summarize_fhir_resource(resource: dict[str, Any]) -> dict[str, Any]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `resource` | yes | `dict[str, Any]` |  | See signature. |

### Returns

`dict[str, Any]`

**See also:** [FHIR module guide](../modules/fhir.md).

## `fyron.fhir.builder.ucum_quantity`

Build a UCUM Quantity.

**Import path:** `fyron.fhir.builder.ucum_quantity`

```python
ucum_quantity(value: int | float, unit: str, code: str | None = None) -> dict[str, Any]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `value` | yes | `int  or  float` |  | See signature. |
| `unit` | yes | `str` |  | See signature. |
| `code` | no | `str  or  None` | `None` | See signature. |

### Returns

`dict[str, Any]`

**See also:** [FHIR module guide](../modules/fhir.md).

## `fyron.fhir.builder.validate_fhir_bundle`

Lightweight structural validation for a FHIR Bundle.

**Import path:** `fyron.fhir.builder.validate_fhir_bundle`

```python
validate_fhir_bundle(bundle: dict[str, Any], version: str = FHIR_R4) -> dict[str, Any]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `bundle` | yes | `dict[str, Any]` |  | See signature. |
| `version` | no | `str` | `FHIR_R4` | See signature. |

### Returns

`dict[str, Any]`

**See also:** [FHIR module guide](../modules/fhir.md).

## `fyron.fhir.builder.validate_fhir_references`

Inspect local references inside a FHIR Bundle without mutating it.

**Import path:** `fyron.fhir.builder.validate_fhir_references`

```python
validate_fhir_references(bundle: dict[str, Any]) -> dict[str, Any]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `bundle` | yes | `dict[str, Any]` |  | See signature. |

### Returns

`dict[str, Any]`

**See also:** [FHIR module guide](../modules/fhir.md).

## `fyron.fhir.builder.validate_fhir_resource`

Lightweight structural validation for a FHIR resource dictionary.

**Import path:** `fyron.fhir.builder.validate_fhir_resource`

```python
validate_fhir_resource(resource: dict[str, Any], version: str = FHIR_R4) -> dict[str, Any]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `resource` | yes | `dict[str, Any]` |  | See signature. |
| `version` | no | `str` | `FHIR_R4` | See signature. |

### Returns

`dict[str, Any]`

**See also:** [FHIR module guide](../modules/fhir.md).

## `fyron.fhir.builder.write_fhir_json`

Write a FHIR JSON payload to disk.

**Import path:** `fyron.fhir.builder.write_fhir_json`

```python
write_fhir_json(payload: dict[str, Any], path: StrPath) -> Path
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `payload` | yes | `dict[str, Any]` |  | See signature. |
| `path` | yes | `StrPath` |  | See signature. |

### Returns

`Path`

**See also:** [FHIR module guide](../modules/fhir.md).

## `fyron.fhir.mapping.build_bundle_from_dataframe`

Dispatch DataFrame-to-FHIR conversion by resource type.

**Import path:** `fyron.fhir.mapping.build_bundle_from_dataframe`

```python
build_bundle_from_dataframe(df: pd.DataFrame, resource_type: str, mapping: dict[str, Any], *, subject_col: str, id_col: str | None = None, study_uid_col: str | None = None, series_uid_col: str | None = None, bundle_type: str = 'collection', transaction_method: str = 'POST', if_none_exist: str | dict[str, str] | None = None, version: str = FHIR_R4) -> dict[str, Any]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `df` | yes | `pd.DataFrame` |  | See signature. |
| `resource_type` | yes | `str` |  | See signature. |
| `mapping` | yes | `dict[str, Any]` |  | See signature. |
| `subject_col` | yes | `str` |  | See signature. |
| `id_col` | no | `str  or  None` | `None` | See signature. |
| `study_uid_col` | no | `str  or  None` | `None` | See signature. |
| `series_uid_col` | no | `str  or  None` | `None` | See signature. |
| `bundle_type` | no | `str` | `'collection'` | See signature. |
| `transaction_method` | no | `str` | `'POST'` | See signature. |
| `if_none_exist` | no | `str  or  dict[str, str]  or  None` | `None` | See signature. |
| `version` | no | `str` | `FHIR_R4` | See signature. |

### Returns

`dict[str, Any]`

**See also:** [FHIR module guide](../modules/fhir.md).

## `fyron.fhir.mapping.build_conditions_from_dataframe`

Build Condition resources and a Bundle from a DataFrame.

**Import path:** `fyron.fhir.mapping.build_conditions_from_dataframe`

```python
build_conditions_from_dataframe(df: pd.DataFrame, mapping: dict[str, Any], *, subject_col: str, id_col: str | None = None, bundle_type: str = 'collection', transaction_method: str = 'POST', if_none_exist: str | dict[str, str] | None = None, version: str = FHIR_R4) -> dict[str, Any]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `df` | yes | `pd.DataFrame` |  | See signature. |
| `mapping` | yes | `dict[str, Any]` |  | See signature. |
| `subject_col` | yes | `str` |  | See signature. |
| `id_col` | no | `str  or  None` | `None` | See signature. |
| `bundle_type` | no | `str` | `'collection'` | See signature. |
| `transaction_method` | no | `str` | `'POST'` | See signature. |
| `if_none_exist` | no | `str  or  dict[str, str]  or  None` | `None` | See signature. |
| `version` | no | `str` | `FHIR_R4` | See signature. |

### Returns

`dict[str, Any]`

**See also:** [FHIR module guide](../modules/fhir.md).

## `fyron.fhir.mapping.build_document_references_from_dataframe`

Build DocumentReference resources and a Bundle from a DataFrame.

**Import path:** `fyron.fhir.mapping.build_document_references_from_dataframe`

```python
build_document_references_from_dataframe(df: pd.DataFrame, mapping: dict[str, Any], *, subject_col: str, id_col: str | None = None, bundle_type: str = 'collection', transaction_method: str = 'POST', if_none_exist: str | dict[str, str] | None = None, version: str = FHIR_R4) -> dict[str, Any]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `df` | yes | `pd.DataFrame` |  | See signature. |
| `mapping` | yes | `dict[str, Any]` |  | See signature. |
| `subject_col` | yes | `str` |  | See signature. |
| `id_col` | no | `str  or  None` | `None` | See signature. |
| `bundle_type` | no | `str` | `'collection'` | See signature. |
| `transaction_method` | no | `str` | `'POST'` | See signature. |
| `if_none_exist` | no | `str  or  dict[str, str]  or  None` | `None` | See signature. |
| `version` | no | `str` | `FHIR_R4` | See signature. |

### Returns

`dict[str, Any]`

**See also:** [FHIR module guide](../modules/fhir.md).

## `fyron.fhir.mapping.build_imaging_measurements_from_dataframe`

Build imaging-measurement resources and a Bundle from a DataFrame.

**Import path:** `fyron.fhir.mapping.build_imaging_measurements_from_dataframe`

```python
build_imaging_measurements_from_dataframe(df: pd.DataFrame, mapping: dict[str, Any], *, subject_col: str, study_uid_col: str, series_uid_col: str | None = None, id_col: str | None = None, bundle_type: str = 'collection', transaction_method: str = 'POST', if_none_exist: str | dict[str, str] | None = None, version: str = FHIR_R4) -> dict[str, Any]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `df` | yes | `pd.DataFrame` |  | See signature. |
| `mapping` | yes | `dict[str, Any]` |  | See signature. |
| `subject_col` | yes | `str` |  | See signature. |
| `study_uid_col` | yes | `str` |  | See signature. |
| `series_uid_col` | no | `str  or  None` | `None` | See signature. |
| `id_col` | no | `str  or  None` | `None` | See signature. |
| `bundle_type` | no | `str` | `'collection'` | See signature. |
| `transaction_method` | no | `str` | `'POST'` | See signature. |
| `if_none_exist` | no | `str  or  dict[str, str]  or  None` | `None` | See signature. |
| `version` | no | `str` | `FHIR_R4` | See signature. |

### Returns

`dict[str, Any]`

**See also:** [FHIR module guide](../modules/fhir.md).

## `fyron.fhir.mapping.build_observations_from_dataframe`

Build Observation resources and a Bundle from a DataFrame.

**Import path:** `fyron.fhir.mapping.build_observations_from_dataframe`

```python
build_observations_from_dataframe(df: pd.DataFrame, mapping: dict[str, Any], *, subject_col: str, id_col: str | None = None, bundle_type: str = 'collection', transaction_method: str = 'POST', if_none_exist: str | dict[str, str] | None = None, version: str = FHIR_R4) -> dict[str, Any]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `df` | yes | `pd.DataFrame` |  | See signature. |
| `mapping` | yes | `dict[str, Any]` |  | See signature. |
| `subject_col` | yes | `str` |  | See signature. |
| `id_col` | no | `str  or  None` | `None` | See signature. |
| `bundle_type` | no | `str` | `'collection'` | See signature. |
| `transaction_method` | no | `str` | `'POST'` | See signature. |
| `if_none_exist` | no | `str  or  dict[str, str]  or  None` | `None` | See signature. |
| `version` | no | `str` | `FHIR_R4` | See signature. |

### Returns

`dict[str, Any]`

**See also:** [FHIR module guide](../modules/fhir.md).

## `fyron.fhir.mapping.extract_coding_summary`

Extract all Coding entries from a resource or Bundle into a DataFrame.

**Import path:** `fyron.fhir.mapping.extract_coding_summary`

```python
extract_coding_summary(payload: dict[str, Any]) -> pd.DataFrame
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `payload` | yes | `dict[str, Any]` |  | See signature. |

### Returns

`pd.DataFrame`

**See also:** [FHIR module guide](../modules/fhir.md).

## `fyron.fhir.mapping.fhir_validation_report`

Return a structured validation report for a FHIR Bundle.

**Import path:** `fyron.fhir.mapping.fhir_validation_report`

```python
fhir_validation_report(bundle: dict[str, Any]) -> dict[str, Any]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `bundle` | yes | `dict[str, Any]` |  | See signature. |

### Returns

`dict[str, Any]`

**See also:** [FHIR module guide](../modules/fhir.md).

## `fyron.fhir.mapping.read_fhir_mapping`

Read a Fyron FHIR mapping JSON file.

**Import path:** `fyron.fhir.mapping.read_fhir_mapping`

```python
read_fhir_mapping(path: StrPath) -> dict[str, Any]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `path` | yes | `StrPath` |  | See signature. |

### Returns

`dict[str, Any]`

**See also:** [FHIR module guide](../modules/fhir.md).

## `fyron.fhir.mapping.validate_coding_systems`

Check coding-system presence and optional allow-list consistency.

**Import path:** `fyron.fhir.mapping.validate_coding_systems`

```python
validate_coding_systems(payload: dict[str, Any], allowed_systems: set[str] | list[str] | None = None) -> dict[str, Any]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `payload` | yes | `dict[str, Any]` |  | See signature. |
| `allowed_systems` | no | `set[str]  or  list[str]  or  None` | `None` | See signature. |

### Returns

`dict[str, Any]`

**See also:** [FHIR module guide](../modules/fhir.md).

## `fyron.fhir.mapping.validate_fhir_mapping`

Validate a Fyron FHIR mapping dictionary and optional source DataFrame.

**Import path:** `fyron.fhir.mapping.validate_fhir_mapping`

```python
validate_fhir_mapping(mapping: dict[str, Any], df: pd.DataFrame | None = None, required_columns: list[str | None] | None = None) -> dict[str, Any]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `mapping` | yes | `dict[str, Any]` |  | See signature. |
| `df` | no | `pd.DataFrame  or  None` | `None` | See signature. |
| `required_columns` | no | `list[str  or  None]  or  None` | `None` | See signature. |

### Returns

`dict[str, Any]`

**See also:** [FHIR module guide](../modules/fhir.md).

## `fyron.fhir.mapping.validate_fhir_mapping_result`

Validate a mapping result object returned by this module.

**Import path:** `fyron.fhir.mapping.validate_fhir_mapping_result`

```python
validate_fhir_mapping_result(result: dict[str, Any]) -> dict[str, Any]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `result` | yes | `dict[str, Any]` |  | See signature. |

### Returns

`dict[str, Any]`

**See also:** [FHIR module guide](../modules/fhir.md).

## `fyron.fhir.mapping.validate_fhir_payload`

Return a structured lightweight validation report for a resource or Bundle.

**Import path:** `fyron.fhir.mapping.validate_fhir_payload`

```python
validate_fhir_payload(payload: dict[str, Any], *, version: str = FHIR_R4, strict: bool = False) -> dict[str, Any]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `payload` | yes | `dict[str, Any]` |  | See signature. |
| `version` | no | `str` | `FHIR_R4` | See signature. |
| `strict` | no | `bool` | `False` | See signature. |

### Returns

`dict[str, Any]`

**See also:** [FHIR module guide](../modules/fhir.md).

## `fyron.fhir.mapping.write_fhir_mapping`

Write a Fyron FHIR mapping JSON file.

**Import path:** `fyron.fhir.mapping.write_fhir_mapping`

```python
write_fhir_mapping(mapping: dict[str, Any], path: StrPath) -> Path
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `mapping` | yes | `dict[str, Any]` |  | See signature. |
| `path` | yes | `StrPath` |  | See signature. |

### Returns

`Path`

**See also:** [FHIR module guide](../modules/fhir.md).

## `fyron.fhir.path_presets.get_fhir_path_preset`

Return a copy of the default FHIRPath extraction preset for a resource.

**Import path:** `fyron.fhir.path_presets.get_fhir_path_preset`

```python
get_fhir_path_preset(resource_type: str) -> list[tuple[str, str]]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `resource_type` | yes | `str` |  | FHIR resource type name, for example ``"Patient"``, ``"Observation"``, ``"Condition"``, or ``"ImagingStudy"``. |

### Returns

`list[tuple[str, str]]` - A mutable list of ``(column_name, fhir_path)`` pairs suitable for ``FHIRRestClient.search_df(..., fhir_paths=...)``.

**See also:** [FHIR module guide](../modules/fhir.md).

## `fyron.fhir.rest.FHIRRestClient`

Simple FHIR REST client focused on bundle retrieval and DataFrame conversion.

**Import path:** `fyron.fhir.rest.FHIRRestClient`

```python
FHIRRestClient(self, base_url: Optional[str] = None, auth_url: Optional[str] = None, auth: Optional[Union[Auth, requests.Session]] = None, num_processes: int = 4, request_timeout: int = 30, request_params: Optional[Dict[str, Any]] = None, bearer_token: Optional[str] = None, log_requests: bool = False, log_request_urls: bool = False, extra_headers: Optional[Dict[str, str]] = None, retries: Optional[Retry] = None, return_fhir_obj: bool = False, token_auth_method: Optional[str] = None, cache_ttl_seconds: int = 300, cache_max_entries: int = 1000, *, worker_auth_timeout: float = 120, parallel_job_timeout: Optional[float] = 300)
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `base_url` | no | `Optional[str]` | `None` | Base FHIR server URL (e.g., https://example.org/fhir). |
| `auth_url` | no | `Optional[str]` | `None` | Token endpoint for password-based auth. If omitted, uses FHIR_AUTH_URL env. |
| `auth` | no | `Optional[Union[Auth, requests.Session]]` | `None` | Optional Auth or requests.Session instance to use. |
| `num_processes` | no | `int` | `4` | Process count for multiprocessing (>=1). |
| `request_timeout` | no | `int` | `30` | Per-request timeout in seconds. |
| `request_params` | no | `Optional[Dict[str, Any]]` | `None` | Default query params merged into every request. |
| `bearer_token` | no | `Optional[str]` | `None` | Token used for parallel requests (or set FHIR_TOKEN env). |
| `log_requests` | no | `bool` | `False` | If True, logs request timing and summaries. |
| `log_request_urls` | no | `bool` | `False` | If True, prints each request URL (with query string) to the console. |
| `extra_headers` | no | `Optional[Dict[str, str]]` | `None` | See signature. |
| `retries` | no | `Optional[Retry]` | `None` | See signature. |
| `return_fhir_obj` | no | `bool` | `False` | See signature. |
| `token_auth_method` | no | `Optional[str]` | `None` | Token auth method for password-based token endpoints ("basic" or "post"). |
| `cache_ttl_seconds` | no | `int` | `300` | In-memory cache TTL for GET responses. |
| `cache_max_entries` | no | `int` | `1000` | Maximum number of cached GET responses. |
| `worker_auth_timeout` | no | `float` | `120` | Positive worker token-wait timeout in seconds (default 120). |
| `parallel_job_timeout` | no | `Optional[float]` | `300` | Positive execution deadline per parallel query in seconds (default 300). Excludes queue time; None disables the overall job deadline. |

### Returns

Class constructor.

**See also:** [FHIR module guide](../modules/fhir.md).

### Public Methods

#### `fyron.fhir.rest.FHIRRestClient.close`

Close the underlying session if owned.

**Import path:** `fyron.fhir.rest.FHIRRestClient.close`

```python
FHIRRestClient.close(self) -> None
```

#### Parameters

No parameters documented.

#### Returns

`None`

**See also:** [FHIR module guide](../modules/fhir.md).

#### `fyron.fhir.rest.FHIRRestClient.fetch_bundles`

Fetch bundles for a resource with pagination.

**Import path:** `fyron.fhir.rest.FHIRRestClient.fetch_bundles`

```python
FHIRRestClient.fetch_bundles(self, resource_type: str, params: Optional[Dict[str, Any]] = None, max_pages: int = -1, show_progress: bool = True) -> Generator[Dict[str, Any], None, int]
```

#### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `resource_type` | yes | `str` |  | FHIR resource type (e.g., Patient, Observation). |
| `params` | no | `Optional[Dict[str, Any]]` | `None` | Query parameters for the search. |
| `max_pages` | no | `int` | `-1` | Maximum number of pages to fetch (-1 for all). |
| `show_progress` | no | `bool` | `True` | Whether to show a tqdm progress bar. |

#### Returns

`Generator[Dict[str, Any], None, int]`

**See also:** [FHIR module guide](../modules/fhir.md).

#### `fyron.fhir.rest.FHIRRestClient.fetch_bundles_parallel`

Fetch bundles for independent searches in completion order.

**Import path:** `fyron.fhir.rest.FHIRRestClient.fetch_bundles_parallel`

```python
FHIRRestClient.fetch_bundles_parallel(self, resource_type: str, param_list: Sequence[Dict[str, Any]], max_pages: int = -1, show_progress: bool = True) -> Generator[Dict[str, Any], None, int]
```

#### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `resource_type` | yes | `str` |  | FHIR resource type. |
| `param_list` | yes | `Sequence[Dict[str, Any]]` |  | One parameter dictionary per query. |
| `max_pages` | no | `int` | `-1` | Per-query page limit, or -1 for all pages. |
| `show_progress` | no | `bool` | `True` | Show completed query progress. |

#### Returns

`Generator[Dict[str, Any], None, int]`

**See also:** [FHIR module guide](../modules/fhir.md).

#### `fyron.fhir.rest.FHIRRestClient.fetch_bundles_partitioned`

Fetch bundles by splitting a broad search into date/time partitions.

**Import path:** `fyron.fhir.rest.FHIRRestClient.fetch_bundles_partitioned`

```python
FHIRRestClient.fetch_bundles_partitioned(self, resource_type: str, partition_param: str, start: Union[str, pd.Timestamp], end: Union[str, pd.Timestamp], params: Optional[Dict[str, Any]] = None, frequency: str = 'YS', window_days: Optional[int] = None, max_pages_per_partition: int = -1, show_progress: bool = True, parallel_fetch: bool = False, auto_sort: bool = True, sort: str = '_id') -> Generator[Dict[str, Any], None, int]
```

#### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `resource_type` | yes | `str` |  | FHIR resource type to search. |
| `partition_param` | yes | `str` |  | Date or dateTime search parameter used for partition windows. |
| `start` | yes | `Union[str, pd.Timestamp]` |  | Inclusive start date for the first partition. |
| `end` | yes | `Union[str, pd.Timestamp]` |  | Exclusive end date for the final partition. |
| `params` | no | `Optional[Dict[str, Any]]` | `None` | Base search parameters merged into every partition. |
| `frequency` | no | `str` | `'YS'` | Pandas-style partition frequency, for example ``YS`` or ``MS``. |
| `window_days` | no | `Optional[int]` | `None` | Optional fixed window size in days; overrides ``frequency``. |
| `max_pages_per_partition` | no | `int` | `-1` | Maximum pages fetched inside each partition. |
| `show_progress` | no | `bool` | `True` | Whether to show progress bars. |
| `parallel_fetch` | no | `bool` | `False` | Whether to fetch partitions in parallel when supported. |
| `auto_sort` | no | `bool` | `True` | Whether to add a stable ``_sort`` parameter when one is missing. |
| `sort` | no | `str` | `'_id'` | Sort field used when ``auto_sort`` is enabled. |

#### Returns

`Generator[Dict[str, Any], None, int]`

**See also:** [FHIR module guide](../modules/fhir.md).

#### `fyron.fhir.rest.FHIRRestClient.bundles_to_dataframe`

Convert bundles to DataFrame(s).

**Import path:** `fyron.fhir.rest.FHIRRestClient.bundles_to_dataframe`

```python
FHIRRestClient.bundles_to_dataframe(self, bundles: Iterable[Dict[str, Any] | FHIRObj], process_function: Optional[ProcessFunc] = None, fhir_paths: Optional[Sequence[Union[str, Tuple[str, str]]]] = None, mode: str = 'flatten', use_multiprocessing: bool = True, per_bundle_metadata: Optional[List[Dict[str, Any]]] = None) -> Union[pd.DataFrame, Dict[str, pd.DataFrame]]
```

#### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `bundles` | yes | `Iterable[Dict[str, Any]  or  FHIRObj]` |  | Iterable of FHIR Bundle JSON objects. |
| `process_function` | no | `Optional[ProcessFunc]` | `None` | Custom processing function. Required when mode="custom". |
| `fhir_paths` | no | `Optional[Sequence[Union[str, Tuple[str, str]]]]` | `None` | FHIRPath expressions to extract fields (requires fhirpathpy). |
| `mode` | no | `str` | `'flatten'` | "flatten" (default) or "custom". |
| `use_multiprocessing` | no | `bool` | `True` | Whether to process bundles with multiprocessing. |
| `per_bundle_metadata` | no | `Optional[List[Dict[str, Any]]]` | `None` | Optional list of dicts, one per bundle; each dict is merged into every row from that bundle (e.g. to attach column_map values). |

#### Returns

`Union[pd.DataFrame, Dict[str, pd.DataFrame]]`

**See also:** [FHIR module guide](../modules/fhir.md).

#### `fyron.fhir.rest.FHIRRestClient.query_to_dataframe_partitioned`

Run a partitioned FHIR search and return DataFrame output.

**Import path:** `fyron.fhir.rest.FHIRRestClient.query_to_dataframe_partitioned`

```python
FHIRRestClient.query_to_dataframe_partitioned(self, resource_type: str, partition_param: str, start: Union[str, pd.Timestamp], end: Union[str, pd.Timestamp], params: Optional[Dict[str, Any]] = None, frequency: str = 'YS', window_days: Optional[int] = None, max_pages_per_partition: int = -1, process_function: Optional[ProcessFunc] = None, fhir_paths: Optional[Sequence[Union[str, Tuple[str, str]]]] = None, mode: str = 'flatten', use_multiprocessing: bool = True, parallel_fetch: bool = False, include_partition_columns: bool = True, deduplicate_by: Optional[Union[str, Sequence[str]]] = None, auto_sort: bool = True, sort: str = '_id', show_progress: bool = True, *, return_report: bool = False) -> Union[pd.DataFrame, Dict[str, Any]]
```

#### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `resource_type` | yes | `str` |  | FHIR resource type to search. |
| `partition_param` | yes | `str` |  | Date or dateTime search parameter used for partition windows. |
| `start` | yes | `Union[str, pd.Timestamp]` |  | Inclusive start date for the first partition. |
| `end` | yes | `Union[str, pd.Timestamp]` |  | Exclusive end date for the final partition. |
| `params` | no | `Optional[Dict[str, Any]]` | `None` | Base search parameters merged into every partition. |
| `frequency` | no | `str` | `'YS'` | Pandas-style partition frequency, for example ``YS`` or ``MS``. |
| `window_days` | no | `Optional[int]` | `None` | Optional fixed window size in days; overrides ``frequency``. |
| `max_pages_per_partition` | no | `int` | `-1` | Maximum pages fetched inside each partition. |
| `process_function` | no | `Optional[ProcessFunc]` | `None` | Custom bundle processing function used in ``custom`` mode. |
| `fhir_paths` | no | `Optional[Sequence[Union[str, Tuple[str, str]]]]` | `None` | FHIRPath expressions to extract columns from each resource. |
| `mode` | no | `str` | `'flatten'` | DataFrame conversion mode, usually ``flatten`` or ``custom``. |
| `use_multiprocessing` | no | `bool` | `True` | Whether bundle-to-table conversion can use multiprocessing. |
| `parallel_fetch` | no | `bool` | `False` | Whether partitions may be fetched in parallel. |
| `include_partition_columns` | no | `bool` | `True` | Whether partition metadata columns are added to result rows. |
| `deduplicate_by` | no | `Optional[Union[str, Sequence[str]]]` | `None` | Optional column or columns used to drop duplicate rows. |
| `auto_sort` | no | `bool` | `True` | Whether to add a stable ``_sort`` parameter when one is missing. |
| `sort` | no | `str` | `'_id'` | Sort field used when ``auto_sort`` is enabled. |
| `show_progress` | no | `bool` | `True` | Whether to show progress bars. |
| `return_report` | no | `bool` | `False` | Return data and per-query completeness tables when True; defaults to False. |

#### Returns

`Union[pd.DataFrame, Dict[str, Any]]`

**See also:** [FHIR module guide](../modules/fhir.md).

#### `fyron.fhir.rest.FHIRRestClient.query_to_dataframe`

Run a query and return DataFrame(s).

**Import path:** `fyron.fhir.rest.FHIRRestClient.query_to_dataframe`

```python
FHIRRestClient.query_to_dataframe(self, resource_type: str, params: Optional[Dict[str, Any]] = None, max_pages: int = -1, process_function: Optional[ProcessFunc] = None, fhir_paths: Optional[Sequence[Union[str, Tuple[str, str]]]] = None, mode: str = 'flatten', use_multiprocessing: bool = True, parallel_params: Optional[Sequence[Dict[str, Any]]] = None, *, return_report: bool = False) -> Union[pd.DataFrame, Dict[str, Any]]
```

#### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `resource_type` | yes | `str` |  | FHIR resource type. |
| `params` | no | `Optional[Dict[str, Any]]` | `None` | Query parameters for a single request flow. |
| `max_pages` | no | `int` | `-1` | Maximum pages to fetch (-1 for all). |
| `process_function` | no | `Optional[ProcessFunc]` | `None` | Custom processing function. |
| `fhir_paths` | no | `Optional[Sequence[Union[str, Tuple[str, str]]]]` | `None` | FHIRPath expressions to extract fields. |
| `mode` | no | `str` | `'flatten'` | "flatten" (default) or "custom". |
| `use_multiprocessing` | no | `bool` | `True` | Whether to process bundles with multiprocessing. |
| `parallel_params` | no | `Optional[Sequence[Dict[str, Any]]]` | `None` | If provided, runs parallel jobs for each param dict. |
| `return_report` | no | `bool` | `False` | Return data and per-query completeness tables when True; defaults to False. |

#### Returns

`Union[pd.DataFrame, Dict[str, Any]]`

**See also:** [FHIR module guide](../modules/fhir.md).

#### `fyron.fhir.rest.FHIRRestClient.query_from_dataframe`

Run one query per DataFrame row and return DataFrame(s).

**Import path:** `fyron.fhir.rest.FHIRRestClient.query_from_dataframe`

```python
FHIRRestClient.query_from_dataframe(self, df: pd.DataFrame, resource_type: str, column_map: Dict[str, str], params: Optional[Dict[str, Any]] = None, max_pages: int = -1, process_function: Optional[ProcessFunc] = None, fhir_paths: Optional[Sequence[Union[str, Tuple[str, str]]]] = None, mode: str = 'flatten', use_multiprocessing: bool = True, parallel_fetch: bool = False, param_prefix: Optional[Dict[str, str]] = None, include_column_map_columns: bool = False, show_progress: bool = True, *, return_report: bool = False) -> Union[pd.DataFrame, Dict[str, Any]]
```

#### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `df` | yes | `pd.DataFrame` |  | Input DataFrame containing query values. |
| `resource_type` | yes | `str` |  | FHIR resource type. |
| `column_map` | yes | `Dict[str, str]` |  | Mapping of FHIR param -> DataFrame column. Column values can be scalars or list-like; lists are sent comma-separated for the same param (e.g. code=a,b). |
| `params` | no | `Optional[Dict[str, Any]]` | `None` | Base query parameters added to each request. Values may be list-like; multiple values are sent comma-separated (e.g. code=a,b). |
| `max_pages` | no | `int` | `-1` | Maximum pages per row (-1 for all). |
| `process_function` | no | `Optional[ProcessFunc]` | `None` | Custom processing function. |
| `fhir_paths` | no | `Optional[Sequence[Union[str, Tuple[str, str]]]]` | `None` | FHIRPath expressions to extract fields. |
| `mode` | no | `str` | `'flatten'` | "flatten" (default) or "custom". |
| `use_multiprocessing` | no | `bool` | `True` | Whether to process bundles with multiprocessing. |
| `parallel_fetch` | no | `bool` | `False` | Whether to fetch bundles in parallel (uses active Auth token or basic auth). |
| `param_prefix` | no | `Optional[Dict[str, str]]` | `None` | Optional mapping of FHIR param -> prefix to prepend to each value (e.g., {"subject": "Patient/"}). |
| `include_column_map_columns` | no | `bool` | `False` | If True, the DataFrame column values used as query params (from column_map) are added as columns to the result so each row can be traced back to the input row. Works with sequential or parallel fetching; original values and input order are preserved. |
| `show_progress` | no | `bool` | `True` | Show completed input-query progress (not resource or page counts). |
| `return_report` | no | `bool` | `False` | Return data and per-query completeness tables when True; defaults to False. |

#### Returns

`Union[pd.DataFrame, Dict[str, Any]]`

**See also:** [FHIR module guide](../modules/fhir.md).

#### `fyron.fhir.rest.FHIRRestClient.query_df`

Short alias for query_to_dataframe.

**Import path:** `fyron.fhir.rest.FHIRRestClient.query_df`

```python
FHIRRestClient.query_df(self, resource_type: str, params: Optional[Dict[str, Any]] = None, max_pages: int = -1, process_function: Optional[ProcessFunc] = None, fhir_paths: Optional[Sequence[Union[str, Tuple[str, str]]]] = None, mode: str = 'flatten', use_multiprocessing: bool = True, parallel_params: Optional[Sequence[Dict[str, Any]]] = None, *, return_report: bool = False) -> Union[pd.DataFrame, Dict[str, Any]]
```

#### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `resource_type` | yes | `str` |  | FHIR resource type. |
| `params` | no | `Optional[Dict[str, Any]]` | `None` | Search parameters for one request flow. |
| `max_pages` | no | `int` | `-1` | Maximum pages to fetch. |
| `process_function` | no | `Optional[ProcessFunc]` | `None` | Custom bundle processing function used in ``custom`` mode. |
| `fhir_paths` | no | `Optional[Sequence[Union[str, Tuple[str, str]]]]` | `None` | FHIRPath expressions to extract columns from each resource. |
| `mode` | no | `str` | `'flatten'` | DataFrame conversion mode, usually ``flatten`` or ``custom``. |
| `use_multiprocessing` | no | `bool` | `True` | Whether bundle-to-table conversion can use multiprocessing. |
| `parallel_params` | no | `Optional[Sequence[Dict[str, Any]]]` | `None` | Optional sequence of parameter dictionaries fetched in parallel. |
| `return_report` | no | `bool` | `False` | Return data and per-query completeness tables when True; defaults to False. |

#### Returns

`Union[pd.DataFrame, Dict[str, Any]]`

**See also:** [FHIR module guide](../modules/fhir.md).

#### `fyron.fhir.rest.FHIRRestClient.search_df`

Friendly FHIR search alias returning DataFrame output.

**Import path:** `fyron.fhir.rest.FHIRRestClient.search_df`

```python
FHIRRestClient.search_df(self, resource_type: str, params: Optional[Dict[str, Any]] = None, max_pages: int = -1, process_function: Optional[ProcessFunc] = None, fhir_paths: Optional[Sequence[Union[str, Tuple[str, str]]]] = None, mode: str = 'flatten', use_multiprocessing: bool = True, parallel_params: Optional[Sequence[Dict[str, Any]]] = None, *, return_report: bool = False) -> Union[pd.DataFrame, Dict[str, Any]]
```

#### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `resource_type` | yes | `str` |  | FHIR resource type. |
| `params` | no | `Optional[Dict[str, Any]]` | `None` | Search parameters for one request flow. |
| `max_pages` | no | `int` | `-1` | Maximum pages to fetch. |
| `process_function` | no | `Optional[ProcessFunc]` | `None` | Custom bundle processing function used in ``custom`` mode. |
| `fhir_paths` | no | `Optional[Sequence[Union[str, Tuple[str, str]]]]` | `None` | FHIRPath expressions to extract columns from each resource. |
| `mode` | no | `str` | `'flatten'` | DataFrame conversion mode, usually ``flatten`` or ``custom``. |
| `use_multiprocessing` | no | `bool` | `True` | Whether bundle-to-table conversion can use multiprocessing. |
| `parallel_params` | no | `Optional[Sequence[Dict[str, Any]]]` | `None` | Optional sequence of parameter dictionaries fetched in parallel. |
| `return_report` | no | `bool` | `False` | Return data and per-query completeness tables when True; defaults to False. |

#### Returns

`Union[pd.DataFrame, Dict[str, Any]]`

**See also:** [FHIR module guide](../modules/fhir.md).

#### `fyron.fhir.rest.FHIRRestClient.query_df_partitioned`

Short alias for query_to_dataframe_partitioned.

**Import path:** `fyron.fhir.rest.FHIRRestClient.query_df_partitioned`

```python
FHIRRestClient.query_df_partitioned(self, resource_type: str, partition_param: str, start: Union[str, pd.Timestamp], end: Union[str, pd.Timestamp], params: Optional[Dict[str, Any]] = None, frequency: str = 'YS', window_days: Optional[int] = None, max_pages_per_partition: int = -1, process_function: Optional[ProcessFunc] = None, fhir_paths: Optional[Sequence[Union[str, Tuple[str, str]]]] = None, mode: str = 'flatten', use_multiprocessing: bool = True, parallel_fetch: bool = False, include_partition_columns: bool = True, deduplicate_by: Optional[Union[str, Sequence[str]]] = None, auto_sort: bool = True, sort: str = '_id', show_progress: bool = True, *, return_report: bool = False) -> Union[pd.DataFrame, Dict[str, Any]]
```

#### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `resource_type` | yes | `str` |  | FHIR resource type to search. |
| `partition_param` | yes | `str` |  | Date or dateTime search parameter used for partition windows. |
| `start` | yes | `Union[str, pd.Timestamp]` |  | Inclusive start date for the first partition. |
| `end` | yes | `Union[str, pd.Timestamp]` |  | Exclusive end date for the final partition. |
| `params` | no | `Optional[Dict[str, Any]]` | `None` | Base search parameters merged into every partition. |
| `frequency` | no | `str` | `'YS'` | Pandas-style partition frequency. |
| `window_days` | no | `Optional[int]` | `None` | Optional fixed window size in days. |
| `max_pages_per_partition` | no | `int` | `-1` | Maximum pages fetched inside each partition. |
| `process_function` | no | `Optional[ProcessFunc]` | `None` | Custom bundle processing function used in ``custom`` mode. |
| `fhir_paths` | no | `Optional[Sequence[Union[str, Tuple[str, str]]]]` | `None` | FHIRPath expressions to extract columns from each resource. |
| `mode` | no | `str` | `'flatten'` | DataFrame conversion mode, usually ``flatten`` or ``custom``. |
| `use_multiprocessing` | no | `bool` | `True` | Whether bundle-to-table conversion can use multiprocessing. |
| `parallel_fetch` | no | `bool` | `False` | Whether partitions may be fetched in parallel. |
| `include_partition_columns` | no | `bool` | `True` | Whether partition metadata columns are added to result rows. |
| `deduplicate_by` | no | `Optional[Union[str, Sequence[str]]]` | `None` | Optional column or columns used to drop duplicate rows. |
| `auto_sort` | no | `bool` | `True` | Whether to add a stable ``_sort`` parameter when one is missing. |
| `sort` | no | `str` | `'_id'` | Sort field used when ``auto_sort`` is enabled. |
| `show_progress` | no | `bool` | `True` | Whether to show progress bars. |
| `return_report` | no | `bool` | `False` | Return data and per-query completeness tables when True; defaults to False. |

#### Returns

`Union[pd.DataFrame, Dict[str, Any]]`

**See also:** [FHIR module guide](../modules/fhir.md).

#### `fyron.fhir.rest.FHIRRestClient.search_df_partitioned`

Friendly alias for partitioned FHIR search returning DataFrames.

**Import path:** `fyron.fhir.rest.FHIRRestClient.search_df_partitioned`

```python
FHIRRestClient.search_df_partitioned(self, resource_type: str, partition_param: str, start: Union[str, pd.Timestamp], end: Union[str, pd.Timestamp], params: Optional[Dict[str, Any]] = None, frequency: str = 'YS', window_days: Optional[int] = None, max_pages_per_partition: int = -1, process_function: Optional[ProcessFunc] = None, fhir_paths: Optional[Sequence[Union[str, Tuple[str, str]]]] = None, mode: str = 'flatten', use_multiprocessing: bool = True, parallel_fetch: bool = False, include_partition_columns: bool = True, deduplicate_by: Optional[Union[str, Sequence[str]]] = None, auto_sort: bool = True, sort: str = '_id', show_progress: bool = True, *, return_report: bool = False) -> Union[pd.DataFrame, Dict[str, Any]]
```

#### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `resource_type` | yes | `str` |  | FHIR resource type to search. |
| `partition_param` | yes | `str` |  | Date or dateTime search parameter used for partition windows. |
| `start` | yes | `Union[str, pd.Timestamp]` |  | Inclusive start date for the first partition. |
| `end` | yes | `Union[str, pd.Timestamp]` |  | Exclusive end date for the final partition. |
| `params` | no | `Optional[Dict[str, Any]]` | `None` | Base search parameters merged into every partition. |
| `frequency` | no | `str` | `'YS'` | Pandas-style partition frequency. |
| `window_days` | no | `Optional[int]` | `None` | Optional fixed window size in days. |
| `max_pages_per_partition` | no | `int` | `-1` | Maximum pages fetched inside each partition. |
| `process_function` | no | `Optional[ProcessFunc]` | `None` | Custom bundle processing function used in ``custom`` mode. |
| `fhir_paths` | no | `Optional[Sequence[Union[str, Tuple[str, str]]]]` | `None` | FHIRPath expressions to extract columns from each resource. |
| `mode` | no | `str` | `'flatten'` | DataFrame conversion mode, usually ``flatten`` or ``custom``. |
| `use_multiprocessing` | no | `bool` | `True` | Whether bundle-to-table conversion can use multiprocessing. |
| `parallel_fetch` | no | `bool` | `False` | Whether partitions may be fetched in parallel. |
| `include_partition_columns` | no | `bool` | `True` | Whether partition metadata columns are added to result rows. |
| `deduplicate_by` | no | `Optional[Union[str, Sequence[str]]]` | `None` | Optional column or columns used to drop duplicate rows. |
| `auto_sort` | no | `bool` | `True` | Whether to add a stable ``_sort`` parameter when one is missing. |
| `sort` | no | `str` | `'_id'` | Sort field used when ``auto_sort`` is enabled. |
| `show_progress` | no | `bool` | `True` | Whether to show progress bars. |
| `return_report` | no | `bool` | `False` | Return data and per-query completeness tables when True; defaults to False. |

#### Returns

`Union[pd.DataFrame, Dict[str, Any]]`

**See also:** [FHIR module guide](../modules/fhir.md).

#### `fyron.fhir.rest.FHIRRestClient.query_df_from`

Short alias for query_from_dataframe.

**Import path:** `fyron.fhir.rest.FHIRRestClient.query_df_from`

```python
FHIRRestClient.query_df_from(self, df: pd.DataFrame, resource_type: str, column_map: Dict[str, str], params: Optional[Dict[str, Any]] = None, max_pages: int = -1, process_function: Optional[ProcessFunc] = None, fhir_paths: Optional[Sequence[Union[str, Tuple[str, str]]]] = None, mode: str = 'flatten', use_multiprocessing: bool = True, parallel_fetch: bool = False, param_prefix: Optional[Dict[str, str]] = None, include_column_map_columns: bool = False, show_progress: bool = True, *, return_report: bool = False) -> Union[pd.DataFrame, Dict[str, Any]]
```

#### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `df` | yes | `pd.DataFrame` |  | Input DataFrame containing query values. |
| `resource_type` | yes | `str` |  | FHIR resource type. |
| `column_map` | yes | `Dict[str, str]` |  | Mapping from FHIR search parameter to DataFrame column. |
| `params` | no | `Optional[Dict[str, Any]]` | `None` | Base query parameters added to every row-wise request. |
| `max_pages` | no | `int` | `-1` | Maximum pages per row. |
| `process_function` | no | `Optional[ProcessFunc]` | `None` | Custom bundle processing function used in ``custom`` mode. |
| `fhir_paths` | no | `Optional[Sequence[Union[str, Tuple[str, str]]]]` | `None` | FHIRPath expressions to extract columns from each resource. |
| `mode` | no | `str` | `'flatten'` | DataFrame conversion mode, usually ``flatten`` or ``custom``. |
| `use_multiprocessing` | no | `bool` | `True` | Whether bundle-to-table conversion can use multiprocessing. |
| `parallel_fetch` | no | `bool` | `False` | Whether row-wise requests may be fetched in parallel. |
| `param_prefix` | no | `Optional[Dict[str, str]]` | `None` | Optional prefixes prepended to row values by FHIR parameter. |
| `include_column_map_columns` | no | `bool` | `False` | Whether input query values are copied into result rows. |
| `show_progress` | no | `bool` | `True` | Show completed input-query progress (not resource or page counts). |
| `return_report` | no | `bool` | `False` | Return data and per-query completeness tables when True; defaults to False. |

#### Returns

`Union[pd.DataFrame, Dict[str, Any]]`

**See also:** [FHIR module guide](../modules/fhir.md).

#### `fyron.fhir.rest.FHIRRestClient.search_df_from`

Friendly row-wise FHIR search alias returning DataFrame output.

**Import path:** `fyron.fhir.rest.FHIRRestClient.search_df_from`

```python
FHIRRestClient.search_df_from(self, df: pd.DataFrame, resource_type: str, column_map: Dict[str, str], params: Optional[Dict[str, Any]] = None, max_pages: int = -1, process_function: Optional[ProcessFunc] = None, fhir_paths: Optional[Sequence[Union[str, Tuple[str, str]]]] = None, mode: str = 'flatten', use_multiprocessing: bool = True, parallel_fetch: bool = False, param_prefix: Optional[Dict[str, str]] = None, include_column_map_columns: bool = False, show_progress: bool = True, *, return_report: bool = False) -> Union[pd.DataFrame, Dict[str, Any]]
```

#### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `df` | yes | `pd.DataFrame` |  | Input DataFrame containing query values. |
| `resource_type` | yes | `str` |  | FHIR resource type. |
| `column_map` | yes | `Dict[str, str]` |  | Mapping from FHIR search parameter to DataFrame column. |
| `params` | no | `Optional[Dict[str, Any]]` | `None` | Base query parameters added to every row-wise request. |
| `max_pages` | no | `int` | `-1` | Maximum pages per row. |
| `process_function` | no | `Optional[ProcessFunc]` | `None` | Custom bundle processing function used in ``custom`` mode. |
| `fhir_paths` | no | `Optional[Sequence[Union[str, Tuple[str, str]]]]` | `None` | FHIRPath expressions to extract columns from each resource. |
| `mode` | no | `str` | `'flatten'` | DataFrame conversion mode, usually ``flatten`` or ``custom``. |
| `use_multiprocessing` | no | `bool` | `True` | Whether bundle-to-table conversion can use multiprocessing. |
| `parallel_fetch` | no | `bool` | `False` | Whether row-wise requests may be fetched in parallel. |
| `param_prefix` | no | `Optional[Dict[str, str]]` | `None` | Optional prefixes prepended to row values by FHIR parameter. |
| `include_column_map_columns` | no | `bool` | `False` | Whether input query values are copied into result rows. |
| `show_progress` | no | `bool` | `True` | Show completed input-query progress (not resource or page counts). |
| `return_report` | no | `bool` | `False` | Return data and per-query completeness tables when True; defaults to False. |

#### Returns

`Union[pd.DataFrame, Dict[str, Any]]`

**See also:** [FHIR module guide](../modules/fhir.md).

#### `fyron.fhir.rest.FHIRRestClient.bundles_to_df`

Short alias for bundles_to_dataframe.

**Import path:** `fyron.fhir.rest.FHIRRestClient.bundles_to_df`

```python
FHIRRestClient.bundles_to_df(self, bundles: Iterable[Dict[str, Any] | FHIRObj], process_function: Optional[ProcessFunc] = None, fhir_paths: Optional[Sequence[Union[str, Tuple[str, str]]]] = None, mode: str = 'flatten', use_multiprocessing: bool = True) -> Union[pd.DataFrame, Dict[str, pd.DataFrame]]
```

#### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `bundles` | yes | `Iterable[Dict[str, Any]  or  FHIRObj]` |  | See signature. |
| `process_function` | no | `Optional[ProcessFunc]` | `None` | See signature. |
| `fhir_paths` | no | `Optional[Sequence[Union[str, Tuple[str, str]]]]` | `None` | See signature. |
| `mode` | no | `str` | `'flatten'` | See signature. |
| `use_multiprocessing` | no | `bool` | `True` | See signature. |

#### Returns

`Union[pd.DataFrame, Dict[str, pd.DataFrame]]`

**See also:** [FHIR module guide](../modules/fhir.md).

#### `fyron.fhir.rest.FHIRRestClient.create_resource`

POST a FHIR resource to ``/{resourceType}``.

**Import path:** `fyron.fhir.rest.FHIRRestClient.create_resource`

```python
FHIRRestClient.create_resource(self, resource: Dict[str, Any], resource_type: Optional[str] = None) -> FHIRWriteResult
```

#### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `resource` | yes | `Dict[str, Any]` |  | See signature. |
| `resource_type` | no | `Optional[str]` | `None` | See signature. |

#### Returns

`FHIRWriteResult`

**See also:** [FHIR module guide](../modules/fhir.md).

#### `fyron.fhir.rest.FHIRRestClient.update_resource`

PUT a FHIR resource to ``/{resourceType}/{id}``.

**Import path:** `fyron.fhir.rest.FHIRRestClient.update_resource`

```python
FHIRRestClient.update_resource(self, resource: Dict[str, Any], resource_id: Optional[str] = None, resource_type: Optional[str] = None) -> FHIRWriteResult
```

#### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `resource` | yes | `Dict[str, Any]` |  | See signature. |
| `resource_id` | no | `Optional[str]` | `None` | See signature. |
| `resource_type` | no | `Optional[str]` | `None` | See signature. |

#### Returns

`FHIRWriteResult`

**See also:** [FHIR module guide](../modules/fhir.md).

#### `fyron.fhir.rest.FHIRRestClient.submit_bundle`

POST a transaction FHIR bundle to the server base URL.

**Import path:** `fyron.fhir.rest.FHIRRestClient.submit_bundle`

```python
FHIRRestClient.submit_bundle(self, bundle: Dict[str, Any]) -> FHIRWriteResult
```

#### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `bundle` | yes | `Dict[str, Any]` |  | See signature. |

#### Returns

`FHIRWriteResult`

**See also:** [FHIR module guide](../modules/fhir.md).

## `fyron.fhir.rest.FHIRWriteResult`

Summary of a FHIR write request.

**Import path:** `fyron.fhir.rest.FHIRWriteResult`

```python
FHIRWriteResult()
```

### Parameters

No parameters documented.

### Returns

Class constructor.

**See also:** [FHIR module guide](../modules/fhir.md).

## `fyron.fhir.rest.QueryJob`

See the signature and linked module guide for context.

**Import path:** `fyron.fhir.rest.QueryJob`

```python
QueryJob()
```

### Parameters

No parameters documented.

### Returns

Class constructor.

**See also:** [FHIR module guide](../modules/fhir.md).

## `fyron.fhir.rest.RepeatedParam`

Represent repeated FHIR search parameters with the same key.

**Import path:** `fyron.fhir.rest.RepeatedParam`

```python
RepeatedParam()
```

### Parameters

No parameters documented.

### Returns

Class constructor.

**See also:** [FHIR module guide](../modules/fhir.md).

## `fyron.fhir.rest.ResponseCache`

Small in-memory TTL cache for GET responses.

**Import path:** `fyron.fhir.rest.ResponseCache`

```python
ResponseCache(self, ttl_seconds: int = 300, max_entries: int = 1000)
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `ttl_seconds` | no | `int` | `300` | See signature. |
| `max_entries` | no | `int` | `1000` | See signature. |

### Returns

Class constructor.

**See also:** [FHIR module guide](../modules/fhir.md).

### Public Methods

#### `fyron.fhir.rest.ResponseCache.get`

See the signature and linked module guide for context.

**Import path:** `fyron.fhir.rest.ResponseCache.get`

```python
ResponseCache.get(self, key: Tuple[Any, ...], now: float) -> Optional[Tuple[Dict[str, Any], str, int, float]]
```

#### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `key` | yes | `Tuple[Any, ...]` |  | See signature. |
| `now` | yes | `float` |  | See signature. |

#### Returns

`Optional[Tuple[Dict[str, Any], str, int, float]]`

**See also:** [FHIR module guide](../modules/fhir.md).

#### `fyron.fhir.rest.ResponseCache.set`

See the signature and linked module guide for context.

**Import path:** `fyron.fhir.rest.ResponseCache.set`

```python
ResponseCache.set(self, key: Tuple[Any, ...], payload: Tuple[Dict[str, Any], str, int, float], now: float) -> None
```

#### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `key` | yes | `Tuple[Any, ...]` |  | See signature. |
| `payload` | yes | `Tuple[Dict[str, Any], str, int, float]` |  | See signature. |
| `now` | yes | `float` |  | See signature. |

#### Returns

`None`

**See also:** [FHIR module guide](../modules/fhir.md).

## `fyron.fhir.rest.build_partition_params`

Build FHIR search parameter sets split by a date/dateTime range.

**Import path:** `fyron.fhir.rest.build_partition_params`

```python
build_partition_params(params: Optional[Dict[str, Any]], partition_param: str, start: Union[str, pd.Timestamp], end: Union[str, pd.Timestamp], *, frequency: str = 'YS', window_days: Optional[int] = None) -> List[Dict[str, Any]]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `params` | yes | `Optional[Dict[str, Any]]` |  | See signature. |
| `partition_param` | yes | `str` |  | See signature. |
| `start` | yes | `Union[str, pd.Timestamp]` |  | See signature. |
| `end` | yes | `Union[str, pd.Timestamp]` |  | See signature. |
| `frequency` | no | `str` | `'YS'` | See signature. |
| `window_days` | no | `Optional[int]` | `None` | See signature. |

### Returns

`List[Dict[str, Any]]`

**See also:** [FHIR module guide](../modules/fhir.md).

## `fyron.fhir.rest.flatten_data`

Flatten bundle entries into row dictionaries by resourceType.

**Import path:** `fyron.fhir.rest.flatten_data`

```python
flatten_data(bundle: Dict[str, Any] | FHIRObj, col_sep: str = '_') -> Dict[str, List[Dict[str, Any]]]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `bundle` | yes | `Dict[str, Any]  or  FHIRObj` |  | See signature. |
| `col_sep` | no | `str` | `'_'` | See signature. |

### Returns

`Dict[str, List[Dict[str, Any]]]`

**See also:** [FHIR module guide](../modules/fhir.md).

## `fyron.fhir.rest.parse_fhir_path`

Extract fields from bundle entries using compiled FHIRPath expressions.

**Import path:** `fyron.fhir.rest.parse_fhir_path`

```python
parse_fhir_path(bundle: Dict[str, Any] | FHIRObj, compiled_fhir_paths: List[Tuple[str, Any]]) -> Dict[str, List[Dict[str, Any]]]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `bundle` | yes | `Dict[str, Any]  or  FHIRObj` |  | See signature. |
| `compiled_fhir_paths` | yes | `List[Tuple[str, Any]]` |  | See signature. |

### Returns

`Dict[str, List[Dict[str, Any]]]`

**See also:** [FHIR module guide](../modules/fhir.md).

## `fyron.fhir.sql.FHIRSQLClient`

Lightweight SQL client for FHIR-backed databases.

**Import path:** `fyron.fhir.sql.FHIRSQLClient`

```python
FHIRSQLClient(self, dsn: Optional[str] = None, host: Optional[str] = None, port: Optional[int] = None, dbname: Optional[str] = None, user: Optional[str] = None, password: Optional[str] = None, sslmode: Optional[str] = None, connect_timeout: int = 10, log_queries: bool = False)
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `dsn` | no | `Optional[str]` | `None` | See signature. |
| `host` | no | `Optional[str]` | `None` | See signature. |
| `port` | no | `Optional[int]` | `None` | See signature. |
| `dbname` | no | `Optional[str]` | `None` | See signature. |
| `user` | no | `Optional[str]` | `None` | See signature. |
| `password` | no | `Optional[str]` | `None` | See signature. |
| `sslmode` | no | `Optional[str]` | `None` | See signature. |
| `connect_timeout` | no | `int` | `10` | See signature. |
| `log_queries` | no | `bool` | `False` | See signature. |

### Returns

Class constructor.

**See also:** [FHIR module guide](../modules/fhir.md).

### Public Methods

#### `fyron.fhir.sql.FHIRSQLClient.close`

Close the database connection.

**Import path:** `fyron.fhir.sql.FHIRSQLClient.close`

```python
FHIRSQLClient.close(self) -> None
```

#### Parameters

No parameters documented.

#### Returns

`None`

**See also:** [FHIR module guide](../modules/fhir.md).

#### `fyron.fhir.sql.FHIRSQLClient.query`

Execute a SQL query and return rows as dicts.

**Import path:** `fyron.fhir.sql.FHIRSQLClient.query`

```python
FHIRSQLClient.query(self, sql: str, params: Optional[Dict[str, Any] | Sequence[Any]] = None) -> List[Dict[str, Any]]
```

#### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `sql` | yes | `str` |  | See signature. |
| `params` | no | `Optional[Dict[str, Any]  or  Sequence[Any]]` | `None` | See signature. |

#### Returns

`List[Dict[str, Any]]`

**See also:** [FHIR module guide](../modules/fhir.md).

#### `fyron.fhir.sql.FHIRSQLClient.query_to_dataframe`

Execute a SQL query and return a DataFrame.

**Import path:** `fyron.fhir.sql.FHIRSQLClient.query_to_dataframe`

```python
FHIRSQLClient.query_to_dataframe(self, sql: str, params: Optional[Dict[str, Any] | Sequence[Any]] = None, rename: Optional[Dict[str, str]] = None) -> pd.DataFrame
```

#### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `sql` | yes | `str` |  | SQL statement with placeholders. |
| `params` | no | `Optional[Dict[str, Any]  or  Sequence[Any]]` | `None` | Optional parameters (dict for named, sequence for positional). |
| `rename` | no | `Optional[Dict[str, str]]` | `None` | Optional mapping to rename columns in the resulting DataFrame. |

#### Returns

`pd.DataFrame`

**See also:** [FHIR module guide](../modules/fhir.md).

#### `fyron.fhir.sql.FHIRSQLClient.query_df`

Backward-compatible alias for query_to_dataframe.

**Import path:** `fyron.fhir.sql.FHIRSQLClient.query_df`

```python
FHIRSQLClient.query_df(self, sql: str, params: Optional[Dict[str, Any] | Sequence[Any]] = None, rename: Optional[Dict[str, str]] = None) -> pd.DataFrame
```

#### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `sql` | yes | `str` |  | See signature. |
| `params` | no | `Optional[Dict[str, Any]  or  Sequence[Any]]` | `None` | See signature. |
| `rename` | no | `Optional[Dict[str, str]]` | `None` | See signature. |

#### Returns

`pd.DataFrame`

**See also:** [FHIR module guide](../modules/fhir.md).

#### `fyron.fhir.sql.FHIRSQLClient.query_df_partitioned`

Run a parameterized SQL query over time/grid partitions.

**Import path:** `fyron.fhir.sql.FHIRSQLClient.query_df_partitioned`

```python
FHIRSQLClient.query_df_partitioned(self, sql: str, *, start: Union[str, pd.Timestamp], end: Union[str, pd.Timestamp], params: Optional[Dict[str, Any]] = None, frequency: str = 'YS', window_days: Optional[int] = None, param_grid: Optional[Mapping[str, Sequence[Any]]] = None, derived_params: Optional[Mapping[str, Callable[[Dict[str, Any]], Any]]] = None, chunksize: int = 10000, rename: Optional[Dict[str, str]] = None, include_partition_columns: bool = True, deduplicate_by: Optional[Union[str, Sequence[str]]] = None, continue_on_error: bool = False, errors: str = 'raise') -> pd.DataFrame
```

#### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `sql` | yes | `str` |  | SQL statement using named placeholders such as ``%(start_ts)s``. |
| `start` | yes | `Union[str, pd.Timestamp]` |  | Inclusive start timestamp for the first partition. |
| `end` | yes | `Union[str, pd.Timestamp]` |  | Exclusive end timestamp for the final partition. |
| `params` | no | `Optional[Dict[str, Any]]` | `None` | Base SQL parameters included in every partition. |
| `frequency` | no | `str` | `'YS'` | Pandas date frequency used to build windows, for example ``YS`` or ``MS``. |
| `window_days` | no | `Optional[int]` | `None` | Fixed partition width in days; overrides ``frequency``. |
| `param_grid` | no | `Optional[Mapping[str, Sequence[Any]]]` | `None` | Optional categorical grid, for example ``{"med": ["heparin"]}``. |
| `derived_params` | no | `Optional[Mapping[str, Callable[[Dict[str, Any]], Any]]]` | `None` | Optional callables that derive additional params from each partition, for example ``med_pattern`` from ``med``. |
| `chunksize` | no | `int` | `10000` | Number of rows per streamed pandas chunk. |
| `rename` | no | `Optional[Dict[str, str]]` | `None` | Optional output column rename mapping. |
| `include_partition_columns` | no | `bool` | `True` | Whether to append partition metadata columns to result rows. |
| `deduplicate_by` | no | `Optional[Union[str, Sequence[str]]]` | `None` | Optional column or columns used to drop duplicate rows. |
| `continue_on_error` | no | `bool` | `False` | Whether failed partitions should be skipped or recorded instead of stopping immediately. |
| `errors` | no | `str` | `'raise'` | ``raise`` to raise failed partitions or ``record`` to append error rows with partition metadata. |

#### Returns

`pd.DataFrame`

**See also:** [FHIR module guide](../modules/fhir.md).

#### `fyron.fhir.sql.FHIRSQLClient.query_df_stream`

Stream a large SQL query as DataFrame chunks.

**Import path:** `fyron.fhir.sql.FHIRSQLClient.query_df_stream`

```python
FHIRSQLClient.query_df_stream(self, sql: str, params: Optional[Dict[str, Any] | Sequence[Any]] = None, rename: Optional[Dict[str, str]] = None, chunksize: int = 10000) -> Iterator[pd.DataFrame]
```

#### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `sql` | yes | `str` |  | See signature. |
| `params` | no | `Optional[Dict[str, Any]  or  Sequence[Any]]` | `None` | See signature. |
| `rename` | no | `Optional[Dict[str, str]]` | `None` | See signature. |
| `chunksize` | no | `int` | `10000` | See signature. |

#### Returns

`Iterator[pd.DataFrame]`

**See also:** [FHIR module guide](../modules/fhir.md).

#### `fyron.fhir.sql.FHIRSQLClient.export_query_partitioned`

Stream partitioned SQL query results to resumable CSV part files.

**Import path:** `fyron.fhir.sql.FHIRSQLClient.export_query_partitioned`

```python
FHIRSQLClient.export_query_partitioned(self, sql: str, output_dir: Union[str, Path], *, start: Union[str, pd.Timestamp], end: Union[str, pd.Timestamp], params: Optional[Dict[str, Any]] = None, frequency: str = 'YS', window_days: Optional[int] = None, param_grid: Optional[Mapping[str, Sequence[Any]]] = None, derived_params: Optional[Mapping[str, Callable[[Dict[str, Any]], Any]]] = None, output_columns: Optional[Sequence[str]] = None, part_filename: str = '{date}.csv', combine_by: Optional[str] = None, combined_filename: str = 'combined_{value}.csv', chunksize: int = 10000, skip_existing: bool = True, continue_on_error: bool = False, rename: Optional[Dict[str, str]] = None) -> pd.DataFrame
```

#### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `sql` | yes | `str` |  | SQL statement using named placeholders such as ``%(start_ts)s``. |
| `output_dir` | yes | `Union[str, Path]` |  | Directory where ``_parts`` and optional combined CSVs are written. |
| `start` | yes | `Union[str, pd.Timestamp]` |  | Inclusive start timestamp for the first partition. |
| `end` | yes | `Union[str, pd.Timestamp]` |  | Exclusive end timestamp for the final partition. |
| `params` | no | `Optional[Dict[str, Any]]` | `None` | Base SQL parameters included in every partition. |
| `frequency` | no | `str` | `'YS'` | Pandas date frequency used to build windows. |
| `window_days` | no | `Optional[int]` | `None` | Fixed partition width in days; overrides ``frequency``. |
| `param_grid` | no | `Optional[Mapping[str, Sequence[Any]]]` | `None` | Optional categorical grid expanded across every time window. |
| `derived_params` | no | `Optional[Mapping[str, Callable[[Dict[str, Any]], Any]]]` | `None` | Optional callables that derive additional params from each partition. |
| `output_columns` | no | `Optional[Sequence[str]]` | `None` | Optional ordered columns to keep in exported CSVs. |
| `part_filename` | no | `str` | `'{date}.csv'` | Relative filename template for partition CSVs. |
| `combine_by` | no | `Optional[str]` | `None` | Optional metadata field used to combine parts, such as ``year``. |
| `combined_filename` | no | `str` | `'combined_{value}.csv'` | Filename template for combined CSVs. |
| `chunksize` | no | `int` | `10000` | Number of rows per streamed pandas chunk. |
| `skip_existing` | no | `bool` | `True` | Whether existing non-empty part files are treated as complete. |
| `continue_on_error` | no | `bool` | `False` | Whether failed partitions should be recorded in the manifest instead of raising immediately. |
| `rename` | no | `Optional[Dict[str, str]]` | `None` | Optional output column rename mapping. |

#### Returns

`pd.DataFrame`

**See also:** [FHIR module guide](../modules/fhir.md).

#### `fyron.fhir.sql.FHIRSQLClient.query_df_parallel`

Run multiple SQL queries in parallel and merge results.

**Import path:** `fyron.fhir.sql.FHIRSQLClient.query_df_parallel`

```python
FHIRSQLClient.query_df_parallel(self, jobs: Sequence[Tuple[str, Optional[Dict[str, Any] | Sequence[Any]]]], rename: Optional[Dict[str, str]] = None, max_workers: Optional[int] = None, merge: str = 'concat', unique_on: Optional[Sequence[str]] = None) -> pd.DataFrame
```

#### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `jobs` | yes | `Sequence[Tuple[str, Optional[Dict[str, Any]  or  Sequence[Any]]]]` |  | List of (sql, params) pairs. |
| `rename` | no | `Optional[Dict[str, str]]` | `None` | Optional mapping to rename output columns. |
| `max_workers` | no | `Optional[int]` | `None` | Number of worker processes (defaults to CPU count). |
| `merge` | no | `str` | `'concat'` | See signature. |
| `unique_on` | no | `Optional[Sequence[str]]` | `None` | See signature. |

#### Returns

`pd.DataFrame`

**See also:** [FHIR module guide](../modules/fhir.md).

#### `fyron.fhir.sql.FHIRSQLClient.query_df_for_keys`

Query PostgreSQL with distinct single or composite cohort keys.

**Import path:** `fyron.fhir.sql.FHIRSQLClient.query_df_for_keys`

```python
FHIRSQLClient.query_df_for_keys(self, df: pd.DataFrame, sql: str, *, key_columns: Sequence[str], params: Optional[Mapping[str, Any]] = None, result_key_columns: Optional[Sequence[str]] = None, chunk_size: int = 1000, parallel: bool = False, max_workers: Optional[int] = None, return_report: bool = False) -> Union[pd.DataFrame, Dict[str, Any]]
```

#### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `df` | yes | `pd.DataFrame` |  | Cohort table; key values must be nonmissing scalar values. |
| `sql` | yes | `str` |  | SQL containing exactly one executable ``{cohort_keys}`` block inside an IN clause. Composite keys use ``(a, b) IN (...)``. |
| `key_columns` | yes | `Sequence[str]` |  | Ordered input key columns. Complete keys are deduplicated. |
| `params` | no | `Optional[Mapping[str, Any]]` | `None` | Additional named scalar parameters; ``_fyron_key_`` is reserved. |
| `result_key_columns` | no | `Optional[Sequence[str]]` | `None` | Ordered output columns corresponding to the input keys. Enables matched/unmatched coverage; values must retain their key types. |
| `chunk_size` | no | `int` | `1000` | Maximum distinct keys per batch, reduced to fit 45,000 parameters. |
| `parallel` | no | `bool` | `False` | Execute batches in separate worker connections when true. |
| `max_workers` | no | `Optional[int]` | `None` | Worker count; defaults to four for parallel execution. |
| `return_report` | no | `bool` | `False` | Return data plus batch rows, a summary, and unmatched keys. |

#### Returns

`pandas.DataFrame or dict` - Database rows, or ``{data, report}`` with report DataFrames. Unmatched means no row returned by this query, not an absent patient. Any failed batch raises; partial results are never returned.

**See also:** [FHIR module guide](../modules/fhir.md).

#### `fyron.fhir.sql.FHIRSQLClient.query_from_dataframe`

Run a query with parameters sourced from a DataFrame.

**Import path:** `fyron.fhir.sql.FHIRSQLClient.query_from_dataframe`

```python
FHIRSQLClient.query_from_dataframe(self, df: pd.DataFrame, sql: str, column_map: Dict[str, str], rename: Optional[Dict[str, str]] = None, param_limit: int = 50000, chunk_size: Optional[int] = None, parallel: bool = False, max_workers: Optional[int] = None, merge: str = 'concat', unique_on: Optional[Sequence[str]] = None, param_style: str = 'positional', param_safety_factor: float = 0.9) -> pd.DataFrame
```

#### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `df` | yes | `pd.DataFrame` |  | Input DataFrame containing values. |
| `sql` | yes | `str` |  | SQL statement with `{name}` placeholder blocks. |
| `column_map` | yes | `Dict[str, str]` |  | Mapping from placeholder name -> DataFrame column name. |
| `rename` | no | `Optional[Dict[str, str]]` | `None` | Optional mapping to rename output columns. |
| `param_limit` | no | `int` | `50000` | Max number of parameters per query (Postgres limit is 65535). |
| `chunk_size` | no | `Optional[int]` | `None` | Optional explicit chunk size for splitting the DataFrame. |
| `parallel` | no | `bool` | `False` | Whether to execute chunks in parallel and merge results. |
| `max_workers` | no | `Optional[int]` | `None` | Number of worker processes when parallel is True. |
| `merge` | no | `str` | `'concat'` | How to merge results: "concat" or "drop_duplicates". |
| `unique_on` | no | `Optional[Sequence[str]]` | `None` | Columns to use for duplicate dropping when merge="drop_duplicates". |
| `param_style` | no | `str` | `'positional'` | "positional" (default) or "named". |
| `param_safety_factor` | no | `float` | `0.9` | Fraction of param_limit used for chunk sizing (0.0-1.0). |

#### Returns

`pd.DataFrame`

**See also:** [FHIR module guide](../modules/fhir.md).

#### `fyron.fhir.sql.FHIRSQLClient.query_df_from`

Short alias for query_from_dataframe.

**Import path:** `fyron.fhir.sql.FHIRSQLClient.query_df_from`

```python
FHIRSQLClient.query_df_from(self, df: pd.DataFrame, sql: str, column_map: Dict[str, str], rename: Optional[Dict[str, str]] = None, param_limit: int = 50000, chunk_size: Optional[int] = None, parallel: bool = False, max_workers: Optional[int] = None, merge: str = 'concat', unique_on: Optional[Sequence[str]] = None, param_style: str = 'positional', param_safety_factor: float = 0.9) -> pd.DataFrame
```

#### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `df` | yes | `pd.DataFrame` |  | See signature. |
| `sql` | yes | `str` |  | See signature. |
| `column_map` | yes | `Dict[str, str]` |  | See signature. |
| `rename` | no | `Optional[Dict[str, str]]` | `None` | See signature. |
| `param_limit` | no | `int` | `50000` | See signature. |
| `chunk_size` | no | `Optional[int]` | `None` | See signature. |
| `parallel` | no | `bool` | `False` | See signature. |
| `max_workers` | no | `Optional[int]` | `None` | See signature. |
| `merge` | no | `str` | `'concat'` | See signature. |
| `unique_on` | no | `Optional[Sequence[str]]` | `None` | See signature. |
| `param_style` | no | `str` | `'positional'` | See signature. |
| `param_safety_factor` | no | `float` | `0.9` | See signature. |

#### Returns

`pd.DataFrame`

**See also:** [FHIR module guide](../modules/fhir.md).

## `fyron.fhir.sql.SQLConfig`

See the signature and linked module guide for context.

**Import path:** `fyron.fhir.sql.SQLConfig`

```python
SQLConfig()
```

### Parameters

No parameters documented.

### Returns

Class constructor.

**See also:** [FHIR module guide](../modules/fhir.md).

## `fyron.fhir.sql.SQLPartition`

One SQL extraction partition with query params and trace metadata.

**Import path:** `fyron.fhir.sql.SQLPartition`

```python
SQLPartition()
```

### Parameters

No parameters documented.

### Returns

Class constructor.

**See also:** [FHIR module guide](../modules/fhir.md).

## `fyron.fhir.sql.build_sql_partitions`

Build SQL partitions with ``start_ts``/``end_ts`` params and metadata.

**Import path:** `fyron.fhir.sql.build_sql_partitions`

```python
build_sql_partitions(*, start: Union[str, pd.Timestamp], end: Union[str, pd.Timestamp], params: Optional[Dict[str, Any]] = None, frequency: str = 'YS', window_days: Optional[int] = None, param_grid: Optional[Mapping[str, Sequence[Any]]] = None, derived_params: Optional[Mapping[str, Callable[[Dict[str, Any]], Any]]] = None) -> List[SQLPartition]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `start` | yes | `Union[str, pd.Timestamp]` |  | Inclusive start timestamp for the first partition. |
| `end` | yes | `Union[str, pd.Timestamp]` |  | Exclusive end timestamp for the final partition. |
| `params` | no | `Optional[Dict[str, Any]]` | `None` | Base SQL parameters copied into every partition. |
| `frequency` | no | `str` | `'YS'` | Pandas date frequency used to build windows. |
| `window_days` | no | `Optional[int]` | `None` | Fixed partition width in days; overrides ``frequency``. |
| `param_grid` | no | `Optional[Mapping[str, Sequence[Any]]]` | `None` | Optional categorical grid expanded across every time window. |
| `derived_params` | no | `Optional[Mapping[str, Callable[[Dict[str, Any]], Any]]]` | `None` | Optional callables that derive additional params from each partition. |

### Returns

`List[SQLPartition]`

**See also:** [FHIR module guide](../modules/fhir.md).

## `fyron.fhir.types.FHIRObj`

Recursively wraps dicts/lists for attribute-style access.

**Import path:** `fyron.fhir.types.FHIRObj`

```python
FHIRObj(self, **kwargs: Any)
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `kwargs` | yes | `Any` |  | See signature. |

### Returns

Class constructor.

**See also:** [FHIR module guide](../modules/fhir.md).

### Public Methods

#### `fyron.fhir.types.FHIRObj.to_json`

Serialize the object to JSON.

**Import path:** `fyron.fhir.types.FHIRObj.to_json`

```python
FHIRObj.to_json(self) -> str
```

#### Parameters

No parameters documented.

#### Returns

`str`

**See also:** [FHIR module guide](../modules/fhir.md).

#### `fyron.fhir.types.FHIRObj.to_dict`

Convert the object to a plain dict.

**Import path:** `fyron.fhir.types.FHIRObj.to_dict`

```python
FHIRObj.to_dict(self) -> Any
```

#### Parameters

No parameters documented.

#### Returns

`Any`

**See also:** [FHIR module guide](../modules/fhir.md).

## `fyron.fhir.utils.extract_condition`

See the signature and linked module guide for context.

**Import path:** `fyron.fhir.utils.extract_condition`

```python
extract_condition(resource: Any) -> Dict[str, Any]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `resource` | yes | `Any` |  | See signature. |

### Returns

`Dict[str, Any]`

**See also:** [FHIR module guide](../modules/fhir.md).

## `fyron.fhir.utils.extract_diagnostic_report`

See the signature and linked module guide for context.

**Import path:** `fyron.fhir.utils.extract_diagnostic_report`

```python
extract_diagnostic_report(resource: Any) -> Dict[str, Any]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `resource` | yes | `Any` |  | See signature. |

### Returns

`Dict[str, Any]`

**See also:** [FHIR module guide](../modules/fhir.md).

## `fyron.fhir.utils.extract_encounter`

See the signature and linked module guide for context.

**Import path:** `fyron.fhir.utils.extract_encounter`

```python
extract_encounter(resource: Any) -> Dict[str, Any]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `resource` | yes | `Any` |  | See signature. |

### Returns

`Dict[str, Any]`

**See also:** [FHIR module guide](../modules/fhir.md).

## `fyron.fhir.utils.extract_imaging_study`

See the signature and linked module guide for context.

**Import path:** `fyron.fhir.utils.extract_imaging_study`

```python
extract_imaging_study(resource: Any, series: Any = None) -> Dict[str, Any]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `resource` | yes | `Any` |  | See signature. |
| `series` | no | `Any` | `None` | See signature. |

### Returns

`Dict[str, Any]`

**See also:** [FHIR module guide](../modules/fhir.md).

## `fyron.fhir.utils.extract_observation`

See the signature and linked module guide for context.

**Import path:** `fyron.fhir.utils.extract_observation`

```python
extract_observation(resource: Any) -> Dict[str, Any]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `resource` | yes | `Any` |  | See signature. |

### Returns

`Dict[str, Any]`

**See also:** [FHIR module guide](../modules/fhir.md).

## `fyron.fhir.utils.extract_patient`

See the signature and linked module guide for context.

**Import path:** `fyron.fhir.utils.extract_patient`

```python
extract_patient(resource: Any) -> Dict[str, Any]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `resource` | yes | `Any` |  | See signature. |

### Returns

`Dict[str, Any]`

**See also:** [FHIR module guide](../modules/fhir.md).

## `fyron.fhir.utils.extract_procedure`

See the signature and linked module guide for context.

**Import path:** `fyron.fhir.utils.extract_procedure`

```python
extract_procedure(resource: Any) -> Dict[str, Any]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `resource` | yes | `Any` |  | See signature. |

### Returns

`Dict[str, Any]`

**See also:** [FHIR module guide](../modules/fhir.md).

## `fyron.fhir.utils.process_condition_bundle`

See the signature and linked module guide for context.

**Import path:** `fyron.fhir.utils.process_condition_bundle`

```python
process_condition_bundle(bundle: Any) -> Dict[str, List[Dict[str, Any]]]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `bundle` | yes | `Any` |  | See signature. |

### Returns

`Dict[str, List[Dict[str, Any]]]`

**See also:** [FHIR module guide](../modules/fhir.md).

## `fyron.fhir.utils.process_diagnostic_report_bundle`

See the signature and linked module guide for context.

**Import path:** `fyron.fhir.utils.process_diagnostic_report_bundle`

```python
process_diagnostic_report_bundle(bundle: Any) -> Dict[str, List[Dict[str, Any]]]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `bundle` | yes | `Any` |  | See signature. |

### Returns

`Dict[str, List[Dict[str, Any]]]`

**See also:** [FHIR module guide](../modules/fhir.md).

## `fyron.fhir.utils.process_encounter_bundle`

See the signature and linked module guide for context.

**Import path:** `fyron.fhir.utils.process_encounter_bundle`

```python
process_encounter_bundle(bundle: Any) -> Dict[str, List[Dict[str, Any]]]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `bundle` | yes | `Any` |  | See signature. |

### Returns

`Dict[str, List[Dict[str, Any]]]`

**See also:** [FHIR module guide](../modules/fhir.md).

## `fyron.fhir.utils.process_imaging_study_bundle`

See the signature and linked module guide for context.

**Import path:** `fyron.fhir.utils.process_imaging_study_bundle`

```python
process_imaging_study_bundle(bundle: Any) -> Dict[str, List[Dict[str, Any]]]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `bundle` | yes | `Any` |  | See signature. |

### Returns

`Dict[str, List[Dict[str, Any]]]`

**See also:** [FHIR module guide](../modules/fhir.md).

## `fyron.fhir.utils.process_observation_bundle`

See the signature and linked module guide for context.

**Import path:** `fyron.fhir.utils.process_observation_bundle`

```python
process_observation_bundle(bundle: Any) -> Dict[str, List[Dict[str, Any]]]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `bundle` | yes | `Any` |  | See signature. |

### Returns

`Dict[str, List[Dict[str, Any]]]`

**See also:** [FHIR module guide](../modules/fhir.md).

## `fyron.fhir.utils.process_patient_bundle`

See the signature and linked module guide for context.

**Import path:** `fyron.fhir.utils.process_patient_bundle`

```python
process_patient_bundle(bundle: Any) -> Dict[str, List[Dict[str, Any]]]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `bundle` | yes | `Any` |  | See signature. |

### Returns

`Dict[str, List[Dict[str, Any]]]`

**See also:** [FHIR module guide](../modules/fhir.md).

## `fyron.fhir.utils.process_procedure_bundle`

See the signature and linked module guide for context.

**Import path:** `fyron.fhir.utils.process_procedure_bundle`

```python
process_procedure_bundle(bundle: Any) -> Dict[str, List[Dict[str, Any]]]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `bundle` | yes | `Any` |  | See signature. |

### Returns

`Dict[str, List[Dict[str, Any]]]`

**See also:** [FHIR module guide](../modules/fhir.md).

## `fyron.fhir.utils.safe_get`

Safely extract a value from nested FHIR JSON or FHIRObj by path.

**Import path:** `fyron.fhir.utils.safe_get`

```python
safe_get(resource: Any, path: str | List[Any] | tuple[Any, ...], default: Any = None) -> Any
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `resource` | yes | `Any` |  | See signature. |
| `path` | yes | `str  or  List[Any]  or  tuple[Any, ...]` |  | See signature. |
| `default` | no | `Any` | `None` | See signature. |

### Returns

`Any`

**See also:** [FHIR module guide](../modules/fhir.md).
