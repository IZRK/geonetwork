const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");

const filters = {};
const moduleStub = {
  directive() { return this; },
  factory() { return this; },
  filter(name, factory) {
    filters[name] = factory;
    return this;
  },
  service() { return this; }
};
const source = fs.readFileSync(
  path.resolve(__dirname, "../../../src/main/resources/catalog/components/utility/UtilityDirective.js"),
  "utf8"
);
vm.runInNewContext(source, {
  angular: { module: () => moduleStub },
  goog: { provide() {} }
});

const thumbnailUrlSize = filters.thumbnailUrlSize();

test("local WebP attachments bypass the unsupported resize endpoint", () => {
  const url = "/geonetwork/api/records/record-1/attachments/cover.WEBP?approved=false";
  assert.equal(thumbnailUrlSize(url), url);
  assert.equal(thumbnailUrlSize(url, 240), url);
});

test("supported local images still request resized thumbnails", () => {
  const url = "/geonetwork/api/records/record-1/attachments/cover.png";
  assert.equal(thumbnailUrlSize(url), `${url}?size=140`);
  assert.equal(thumbnailUrlSize(`${url}?approved=false`, 240),
    `${url}?approved=false&size=240`);
});

test("external image URLs and empty URLs stay unchanged", () => {
  const url = "https://images.example.org/cover.webp";
  assert.equal(thumbnailUrlSize(url), url);
  assert.equal(thumbnailUrlSize(""), "");
});
