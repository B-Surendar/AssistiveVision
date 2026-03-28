import React from "react";
import { DetectedObject } from "../types";

interface Props {
  objects: DetectedObject[];
}

const DIRECTION_ICON: Record<string, string> = {
  approaching: "▼",
  "moving away": "▲",
  stationary: "●",
};

const DIRECTION_CLASS: Record<string, string> = {
  approaching: "dir-approaching",
  "moving away": "dir-away",
  stationary: "dir-static",
};

function distanceColor(d: number): string {
  if (d < 1.5) return "dist-danger";
  if (d < 3.0) return "dist-warn";
  return "dist-safe";
}

const ObjectList: React.FC<Props> = ({ objects }) => {
  if (!objects.length) {
    return (
      <section className="objects-panel">
        <div className="objects-header">
          <span aria-hidden="true">◇</span> Detected Objects
        </div>
        <p className="objects-empty">No objects detected</p>
      </section>
    );
  }

  return (
    <section className="objects-panel" aria-label="Detected objects">
      <div className="objects-header">
        <span aria-hidden="true">◇</span> Detected Objects
        <span className="obj-count">{objects.length}</span>
      </div>
      <ul className="objects-list" role="list">
        {objects.map((obj) => (
          <li key={obj.id} className="obj-row" role="listitem">
            <span
              className={`dir-icon ${DIRECTION_CLASS[obj.direction] ?? "dir-static"}`}
              aria-label={obj.direction}
            >
              {DIRECTION_ICON[obj.direction] ?? "●"}
            </span>
            <span className="obj-label">{obj.label}</span>
            <span className={`obj-dist ${distanceColor(obj.distance_m)}`}>
              {obj.distance_m.toFixed(1)} m
            </span>
            <span className="obj-direction">{obj.direction}</span>
            <div
              className="conf-bar-wrap"
              title={`Confidence: ${(obj.confidence * 100).toFixed(0)}%`}
            >
              <div
                className="conf-bar-fill"
                style={{ width: `${obj.confidence * 100}%` }}
                role="progressbar"
                aria-valuenow={obj.confidence * 100}
                aria-valuemin={0}
                aria-valuemax={100}
              />
            </div>
          </li>
        ))}
      </ul>
    </section>
  );
};

export default ObjectList;
