const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const test = require("node:test");

const registrations = {};
const angularModule = {
  directive(name, definition) {
    registrations[name] = definition;
    return this;
  },
  factory() {
    return this;
  },
  filter() {
    return this;
  },
  service() {
    return this;
  }
};

const context = {
  angular: { module: () => angularModule },
  goog: { provide() {} }
};
const source = fs.readFileSync(
  path.resolve(
    __dirname,
    "../../../src/main/resources/catalog/components/utility/UtilityDirective.js"
  ),
  "utf8"
);
vm.runInNewContext(source, context);

const definition = registrations.gnImgModal[
  registrations.gnImgModal.length - 1
](name => (value => value));
const imageUrl = "/geonetwork/api/records/eml-record/attachments/overview.png";

function openModal({ model = { uuid: "eml-record" }, src = imageUrl, ngSrc } = {}) {
  let clickHandler;
  let modalMarkup;
  let hideCount = 0;
  let captionText;
  const modalAttributes = {};
  const imageAttributes = {};
  const controlEvents = {};
  const modalEvents = {};
  const viewportEvents = {};
  const modalDom = {};
  const viewportDom = {};
  const imageDom = { complete: false };
  const imageCollection = {
    0: imageDom,
    first() {
      return this;
    },
    attr(name, value) {
      imageAttributes[name] = value;
      return this;
    },
    on() {
      return this;
    }
  };
  const controls = {
    on(eventName, handler) {
      controlEvents[eventName] = handler;
      return this;
    },
    text(value) {
      captionText = value;
      return this;
    }
  };
  const viewport = {
    0: viewportDom,
    on(eventName, handler) {
      viewportEvents[eventName] = handler;
      return this;
    },
    width: () => 800,
    height: () => 600,
    scrollTop() {
      return this;
    },
    scrollLeft() {
      return this;
    }
  };
  const modal = {
    0: modalDom,
    attr(name, value) {
      modalAttributes[name] = value;
      return this;
    },
    modal(action) {
      if (action === "hide") {
        hideCount++;
      }
      return this;
    },
    on(eventName, handler) {
      modalEvents[eventName] = handler;
      return this;
    },
    find(selector) {
      if (selector === ".gn-img-modal-viewport") {
        return viewport;
      }
      if (selector === "img") {
        return imageCollection;
      }
      return controls;
    }
  };

  context.document = { body: {} };
  context.$ = () => ({ append() {} });
  context.angular.element = markup => {
    modalMarkup = markup;
    return modal;
  };

  definition.link(
    { $eval: () => model },
    {
      bind: (event, handler) => {
        assert.equal(event, "click");
        clickHandler = handler;
      },
      attr: name => (name === "src" ? src : undefined)
    },
    { gnImgModal: "md", ngSrc }
  );

  assert.equal(typeof clickHandler, "function");
  clickHandler();
  return {
    modalMarkup,
    modalAttributes,
    imageAttributes,
    captionText,
    imageDom,
    controlEvents,
    modalEvents,
    viewportEvents,
    modalDom,
    viewportDom,
    get hideCount() {
      return hideCount;
    }
  };
}

test("opens the clicked image when its EML overview is not indexed", () => {
  const result = openModal();
  assert.equal(result.imageAttributes.src, imageUrl);
  assert.equal(result.modalAttributes.id, `gn-img-modal-${imageUrl}`);
  assert.match(result.modalMarkup, /class="modal fade in(?:\s|\")/);
  assert.doesNotMatch(result.modalMarkup, new RegExp(imageUrl));
  assert.match(result.modalMarkup, /gn-img-modal-viewport/);
  assert.match(result.modalMarkup, /gn-img-zoom-out/);
  assert.match(result.modalMarkup, /gn-img-zoom-in/);
  assert.match(result.modalMarkup, /×<\/button>/);
  assert.doesNotMatch(result.modalMarkup, /<i class="fa /);
  result.modalEvents.click({ target: result.modalDom });
  result.viewportEvents.click({ target: result.viewportDom });
  assert.equal(result.hideCount, 2);
  result.viewportEvents.click({ target: result.imageDom });
  assert.equal(result.hideCount, 2);
});

test("keeps a quoted metadata image URL out of parsed modal markup", () => {
  const url = 'https://images.example/cover.png" onerror="alert(1)';
  const result = openModal({ src: url });

  assert.equal(result.imageAttributes.src, url);
  assert.equal(result.modalAttributes.id, `gn-img-modal-${url}`);
  assert.doesNotMatch(result.modalMarkup, /images\.example|onerror/);
});

test("preserves thumbnail URL precedence without parsing it as HTML", () => {
  const thumbnail = '/api/records/record/attachments/thumbnail.png" onerror="alert(1)';
  const fullImage = "/api/records/record/attachments/full.png";
  const result = openModal({
    model: { id: "record", lUrl: fullImage },
    src: thumbnail,
    ngSrc: thumbnail
  });

  assert.equal(result.imageAttributes.src, thumbnail);
  assert.equal(result.modalAttributes.id, "gn-img-modal-record");
  assert.doesNotMatch(result.modalMarkup, /onerror/);
});

test("sets WMS image IDs and captions as values rather than HTML", () => {
  const id = 'legend" onclick="alert(1)';
  const label = '<img src=x onerror="alert(1)">';
  const url = "https://images.example/legend.png";
  const result = openModal({ model: { id, url, title: label }, src: null });

  assert.equal(result.modalAttributes.id, `gn-img-modal-${id}`);
  assert.equal(result.imageAttributes.src, url);
  assert.equal(result.imageAttributes.alt, label);
  assert.equal(result.captionText, label);
  assert.doesNotMatch(result.modalMarkup, /alert\(1\)|<img src=x/);
});
