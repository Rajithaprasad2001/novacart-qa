# NovaCart QA package
pip install -r requirements.txt -r requirements-test.txt && playwright install chromium
pytest tests --cov=app --cov-branch      # unit, functional, security, decision-table (16 xfail = known open defects BUG-01..13)
behave features                          # BDD (Gherkin)
pytest tests_ui                          # Playwright UI automation (screenshots -> evidence/)
locust -f locustfile.py --headless -u 100 -r 100 -t 20s --host http://127.0.0.1:5000
radon cc app.py -s -a ; bandit -r app.py ; flake8 app.py --max-line-length=100
SonarQube: run sonar-scanner with sonar-project.properties (coverage.xml included)
patches/ holds the verified fix for BUG-06.
pytest tests_selenium                    # Selenium WebDriver UI automation (headless Chrome, screenshots -> evidence/selenium_*.png)
jmeter -n -t jmeter/novacart_load.jmx -Jhost=127.0.0.1 -Jport=5000 -l jmeter/results.jtl -e -o evidence/jmeter_report   # JMeter 10/50/100 users
python tools/snap.py shot <url> <out.png> [--full] [--wait-for css]    # evidence screenshots (Playwright, 1440x900)
python tools/snap.py sonar <url> <out.png>                               # same, after logging into local SonarQube (creds in ~/.novacart_auth/)
