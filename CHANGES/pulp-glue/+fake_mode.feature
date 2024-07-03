Implemented a `fake_mode` flag on the `PulpContext` that indicates to users of the context that modifying operations should not be carried out, but faked.
This will imply the `safe_calls_only` flag in the `api_kwargs` that will serve as a safeguard for any POST, PUT, PATCH or DELETE that still made it through.
A `NotImplementedFake` exception will be issued in that case.
