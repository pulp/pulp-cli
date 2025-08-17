Taught resource-option and href-lookup to accept PRNs if post-core-3.63.

NOTE: this does *not* affect `pulp show --href` - there isn't enough information to
use PRNs in that context, until pulpcore allows "naked" PRN GETs.
