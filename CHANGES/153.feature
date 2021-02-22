In pulpcore 3.11, the component names changed to fix a bug. This ported ``pulp-cli`` to use the new
names and provides dictionary named ``new_component_names_to_pre_3_11_names`` in the
``pulpcore.cli.common.context`` module which provides new to old name mappings for a fallback
support. ``pulp-cli`` plugins can add to this list by importing and modifying that dictionary also.
