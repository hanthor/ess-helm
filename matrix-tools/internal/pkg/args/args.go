// Copyright 2025 New Vector Ltd
//
// SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-Element-Commercial

package args

import (
	"flag"
	"strings"
)

type Options struct {
	Files   []string
	Output  string
	Address string
}

func ParseArgs(args []string) (*Options, error) {
	var options Options

	renderConfigSet := flag.NewFlagSet("render-config", flag.ExitOnError)
	output := renderConfigSet.String("output", "", "Output file for rendering")

	tcpWaitSet := flag.NewFlagSet("tcpwait", flag.ExitOnError)
	tcpWait := tcpWaitSet.String("address", "", "Address to listen on for TCP connections")

	if args[1] == "render-config" {
		err := renderConfigSet.Parse(args[2:])
		if err != nil {
			return nil, err
		}
	} else if args[1] == "tcpwait" {
		err := tcpWaitSet.Parse(args[2:])
		if err != nil {
			return nil, err
		}
	} else {
		return nil, flag.ErrHelp
	}

	if *tcpWait != "" {
		options.Address = *tcpWait
	}
	for _, file := range renderConfigSet.Args() {
		if strings.HasPrefix(file, "-") {
			return nil, flag.ErrHelp
		}
		options.Files = append(options.Files, file)
	}
	options.Output = *output
	return &options, nil
}
