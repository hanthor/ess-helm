// Copyright 2025 New Vector Ltd
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-Element-Commercial

package main

import (
	"fmt"
	"os"

	"flag"

	"github.com/element-hq/ess-helm/matrix-tools/internal/pkg/args"
	"github.com/element-hq/ess-helm/matrix-tools/internal/pkg/renderer"
	"github.com/element-hq/ess-helm/matrix-tools/internal/pkg/tcpwait"
	"gopkg.in/yaml.v3"
)

func main() {
	options, err := args.ParseArgs(os.Args)
	if err != nil {
		fmt.Println(err)
		return
	}
	result, err := renderer.RenderConfig(options.Files)
	if err != nil {
		if err == flag.ErrHelp {
			flag.CommandLine.Usage()
		} else {
			fmt.Println("Error:", err)
		}
		os.Exit(1)
	}

	if options.Address != "" {
		tcpwait.WaitForTCP(options.Address)
	}

	if options.Output != "" && len(options.Files) > 0 {
		outputYAML, _ := yaml.Marshal(result)
		fmt.Printf("Rendering config to file: %v", options.Output)
		err = os.WriteFile(options.Output, outputYAML, 0644)
		if err != nil {
			fmt.Println("Error writing to file:", err)
			os.Exit(1)
		}
	}

}
