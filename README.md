# fetcher-py

Provides generalized fetcher for retrieving package metadata, and
package artifact from the registry.

It has, 
- command line interface
- ~automatic retries~ (in development)
- ~request/response caching~~ (in development)
- ~authenticated/private requests~ (in development)
- ~selection strategy, when resolving from multiple registries~ (in development)
- ~machine-readable persistance~ (in development)

It is designed for hacky automation in mind.

### usage (as command line app)

```bash
# install using pipx, refer to: https://pipx.pypa.io/stable/
; pipx install git+https://github.com/ezkangaroo/fetcher-py.git

# run the app
; fetcher_py --help
```

### usage (as library)

```bash
; poetry add git+https://github.com/ezkangaroo/fetcher-py.git
```

```python
import requests
from fetcher_py.fetcher import Fetcher

# make fetcher
session = requests.session()
fetcher = Fetcher(session)

# get metadata
component = fetcher.get("pip://numpy@1.0")
print('component', component)

# get in memory
io_bytes_of_zipfile = fetcher.download_raw("pip://numpy@1.0")

# download to disk
fetcher.download("pip://numpy@1.0", "some/local/path/to/dir")
```

### supported registry or kinds

- pypi (`pip://name[@version]`)
- npm (`pip://name[@version]`)
- crate (`cargo://name[@version]`)
- gem (`gem://name[@version]`)
- haskell (`hackage://name[@version]`)
- perl (`cpan://name[@version]`)
- http (`http://name[@version]`)
- https (`https://name[@version]`)
- composer (`composer://vendor/name[@version]`)
- nuget (`nuget://name[@version]`)
- brew (`brew://name`) (version is not supported it will be ignored)
- oci (`oci://name:version`) e.g. `oci://ghcr.io/wolfv/conda-forge/linux-64/xtensor:0.9.0-0`
- git (`git://<git-clone-url>@hashOrTagOrBenach`) e.g. `git://https://github.com/sharkdp/bat.git@v0.21.0`

# roadmap
- support oci image with image index (image with many platforms)
- allow providing custom registry
- support www-auth, and token based auth for private registeries
- extend registry to accept kwargs
- extends default session to have retries
- golang modules
- maven
- cocopods
- cleanup code in git
- cleanup code in brew
- cleanup code in nuget