from locust import HttpUser, task, between


class Shopper(HttpUser):
    wait_time = between(0.1, 0.5)

    @task(5)
    def browse(self):
        self.client.get("/")

    @task(3)
    def search(self):
        self.client.get("/?q=watch&sort=price_asc")

    @task(2)
    def detail(self):
        self.client.get("/product/1")

    @task(1)
    def add_cart(self):
        self.client.post("/cart/add/4", data={"quantity": "1"})
        self.client.get("/cart")
