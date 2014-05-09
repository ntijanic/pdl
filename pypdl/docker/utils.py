

def find_image(client, repo, tag='latest'):
    images = client.images(repo)
    images = filter(lambda x: (repo + ':' + tag) in x['RepoTags'], images)
    return (images or [None])[0]


def parse_repository_tag(repo):
    column_index = repo.rfind(':')
    if column_index < 0:
        return repo, ""
    tag = repo[column_index+1:]
    slash_index = tag.find('/')
    if slash_index < 0:
        return repo[:column_index], tag

    return repo, ""
