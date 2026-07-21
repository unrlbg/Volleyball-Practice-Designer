(() => {
  "use strict";

  const api = {
    screenToWorkspace(point, panX, panY, zoom) {
      return {
        x: (point.x - panX) / zoom,
        y: (point.y - panY) / zoom
      };
    },
    clientToWorkspace(svg, viewport, clientX, clientY) {
      const point = svg.createSVGPoint();
      point.x = clientX;
      point.y = clientY;
      return point.matrixTransform(viewport.getScreenCTM().inverse());
    },
    delta(start, current) {
      return { x: current.x - start.x, y: current.y - start.y };
    },
    normalizeAngle(angle) {
      return ((Number(angle) % 360) + 360) % 360;
    },
    shortestAngleDelta(from, to) {
      return ((Number(to) - Number(from) + 540) % 360) - 180;
    },
    rotatePoint(point, center, degrees) {
      const radians = Number(degrees) * Math.PI / 180;
      const dx = point.x - center.x;
      const dy = point.y - center.y;
      return {
        x: center.x + dx * Math.cos(radians) - dy * Math.sin(radians),
        y: center.y + dx * Math.sin(radians) + dy * Math.cos(radians)
      };
    },
    snapAngle(angle, shiftKey = false) {
      const normalized = api.normalizeAngle(angle);
      if (shiftKey) return api.normalizeAngle(Math.round(normalized / 15) * 15);
      const cardinal = [0, 90, 180, 270, 360].find(value => Math.abs(normalized - value) <= 4);
      return cardinal === undefined ? Math.round(normalized) : api.normalizeAngle(cardinal);
    },
    rotatedRectCorners(center, width, height, rotation) {
      return [
        { x: center.x - width / 2, y: center.y - height / 2 },
        { x: center.x + width / 2, y: center.y - height / 2 },
        { x: center.x + width / 2, y: center.y + height / 2 },
        { x: center.x - width / 2, y: center.y + height / 2 }
      ].map(point => api.rotatePoint(point, center, rotation));
    },
    boundsFromPoints(points, padding = 0) {
      const xs = points.map(point => point.x);
      const ys = points.map(point => point.y);
      const minX = Math.min(...xs) - padding;
      const minY = Math.min(...ys) - padding;
      const maxX = Math.max(...xs) + padding;
      const maxY = Math.max(...ys) + padding;
      return { x: minX, y: minY, w: maxX - minX, h: maxY - minY };
    },
    canMove(object) {
      return !!object && object.locked !== true;
    }
  };

  window.VPDInteraction = Object.freeze(api);
})();
