from celery_app import celery_app


def test_deepresearch_tasks_are_routed_to_dedicated_queue():
    router = celery_app.amqp.router

    generate_route = router.route(
        {},
        "app.tasks.deepresearch_tasks.generate_analysts_task",
        args=(),
        kwargs={},
    )
    research_route = router.route(
        {},
        "app.tasks.deepresearch_tasks.run_deepresearch_task",
        args=(),
        kwargs={},
    )

    assert generate_route["queue"].name == "deepresearch"
    assert research_route["queue"].name == "deepresearch"
