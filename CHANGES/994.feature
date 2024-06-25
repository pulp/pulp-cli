Added --directory to `rpm content -t package upload`.

This finds all *.rpm in the specified directory and arranges for
them to be added to the specified --repository, and then publishes
the final resulting repository-version.
