jte {
    pipeline_template = 'k8s_build.groovy'
}

libraries {
    git {
        repo_url = 'https://github.com/livelace/webchela.git'
    }
    mattermost
    nexus {
       source = 'dist/webchela-1.5.2-py3.8.egg'
       destination = 'dists-internal/webchela/webchela-1.5.2-py3.8.egg'
    }
    python
}

keywords {
    build_image = 'harbor-core.k8s-2.livelace.ru/infra/service-core:latest'
}
