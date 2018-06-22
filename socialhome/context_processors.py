from socialhome.models import PolicyDocument


def policy_documents(request):
    """
    Add to context status of published policy documents.
    """
    docs = PolicyDocument.objects.filter(published_version__isnull=False).values('type')
    policy_docs = {
        'privacypolicy': False,
        'tos': False,
    }
    for doc in docs:
        policy_docs[doc['type'].value] = True
    return {'policy_docs': policy_docs}
