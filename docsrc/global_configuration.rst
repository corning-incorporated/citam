======================
Global Configuration
======================


-------------------------
Dashboard Configuration
-------------------------

*Required*

:CITAM_RESULT_PATH: The local results directory. To view multiple results in the
    dashboard, set **CITAM_RESULT_PATH** to a parent directory. This is only used
    by :class:`citam.api.storage.local.LocalStorageDriver`


*Optional*
The following settings can be set using environment variables can be used

:CITAM_STORAGE_DRIVER: The storage backend to use.  Current options are
    :class:`citam.api.storage.ceph.CephStorageDriver` and
    :class:`citam.api.storage.local.LocalStorageDriver`

:CITAM_STORAGE_KEY: The s3 storage access key.  This is only used by
    :class:`citam.api.storage.ceph.CephStorageDriver`

:CITAM_STORAGE_SECRET: The s3 storage secret key.  This is only used by
    :class:`citam.api.storage.ceph.CephStorageDriver`

:CITAM_STORAGE_BUCKET: The s3 storage access key.  This is only used by
    :class:`citam.api.storage.ceph.CephStorageDriver`

:CITAM_STORAGE_REGION: The s3 storage region.  This is only used by
   :class:`citam.api.storage.ceph.CephStorageDriver`

:CITAM_STORAGE_URL: The filesystem path to model results.  This is only used
    by :class:`citam.api.storage.ceph.CephStorageDriver`


:CITAM_LOG_LEVEL: Application logging level.
    Options are: DEBUG, INFO, WARNING, ERROR, CRITICAL
