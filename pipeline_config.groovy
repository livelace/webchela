libraries {
    dependency_check
    dependency_track {
        project = "webchela"
        version = "master"
    }
    git {
        repo_url = "https://github.com/livelace/webchela.git"
    }
    harbor_replicate {
        policy = "webchela"
    }
    k8s_build {
        image = "harbor-core.k8s-2.livelace.ru/infra/service-core:latest"
    }
    kaniko {
        destination = "data/webchela:latest"
    }
    mattermost
    nexus {
       source = "dist/webchela-1.5.2-py3.8.egg"
       destination = "dists-internal/webchela/webchela-1.5.2-py3.8.egg"
    }
    python
    sonarqube
}
